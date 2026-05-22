import os
import re
import json
import time
import hashlib
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# In-memory cache for LLM responses (keyed by text hash)
# Prevents duplicate API calls for the same report content
_llm_cache: dict[str, dict] = {}
_CACHE_MAX_SIZE = 50


def _get_cache_key(raw_text: str) -> str:
    """Generate a cache key from the first 8000 chars of report text."""
    return hashlib.sha256(raw_text[:8000].encode()).hexdigest()


def _try_llm_parse(raw_text: str) -> dict | None:
    """Attempt to parse the credit report using Gemini API. Returns None on failure."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "placeholder":
        return None

    # Check cache first
    cache_key = _get_cache_key(raw_text)
    if cache_key in _llm_cache:
        logger.info("LLM cache hit, returning cached result")
        return _llm_cache[cache_key]

    try:
        from openai import OpenAI, RateLimitError, APIError

        base_url = os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
        model = os.environ.get("OPENAI_MODEL", "gemini-2.0-flash")

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=60,
        )

        prompt = """You are a credit report analysis expert for Indian credit bureaus (CIBIL, Experian, Equifax, CRIF).
Analyze the following credit report text and return a JSON object with this exact schema:
{
  "score": <integer between 300-900, or null if not found>,
  "customer_name": <string, or "Valued Customer" if not found>,
  "general_health": <string describing overall credit health>,
  "issues": [
    {
      "account": <account name>,
      "type": "Red" or "Yellow" or "Green",
      "details": <what is wrong, max 140 chars>,
      "action": <specific action to take>,
      "impact": "High" or "Medium" or "Low"
    }
  ],
  "action_steps": [<list of actionable strings, max 5>],
  "timeline": [
    {"phase": <e.g. "Month 1">, "task": <description>, "status": "Critical" or "In Progress" or "Target"}
  ]
}

Rules:
- Score: Look for CIBIL/credit score, typically 3 digits (300-900). If multiple scores found, use the main CIBIL score.
- Issues: Only include actual problems found in the report. Do NOT fabricate issues.
- Account names: Use Title Case, preserve bank acronyms (HDFC, SBI, ICICI, etc.).
- Action steps: Be specific and actionable. Maximum 5 steps.
- Timeline: 2-4 phases covering immediate to 6-month recovery.
- If no issues found, return empty issues array.
- Output ONLY valid JSON, no markdown, no explanations."""

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nCREDIT REPORT TEXT:\n{raw_text[:8000]}"},
                ],
                temperature=0.1,
                max_tokens=2048,
            )
        except RateLimitError:
            logger.warning("Gemini rate limit hit. Falling back to regex parser.")
            return None
        except APIError as e:
            logger.error(f"Gemini API error: {e}. Falling back to regex parser.")
            return None

        content = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content.rsplit("\n```", 1)[0]
            content = content.strip()
            if content.startswith("json"):
                content = content[4:].strip()

        result = json.loads(content)

        # Validate and sanitize
        result["score"] = max(300, min(900, int(result.get("score", 650))))
        result["customer_name"] = str(result.get("customer_name", "Valued Customer")).strip() or "Valued Customer"
        result["general_health"] = str(result.get("general_health", "Needs Attention"))
        result["issues"] = result.get("issues", [])[:10]
        result["action_steps"] = list(dict.fromkeys(result.get("action_steps", [])))[:7]
        result["timeline"] = result.get("timeline", [])

        # Cache the result
        if len(_llm_cache) >= _CACHE_MAX_SIZE:
            oldest_key = next(iter(_llm_cache))
            del _llm_cache[oldest_key]
        _llm_cache[cache_key] = result

        return result

    except Exception as e:
        logger.error(f"LLM parse failed, falling back to regex: {e}")
        return None


def clear_llm_cache():
    """Clear the LLM response cache. Useful for testing."""
    _llm_cache.clear()


def generate_credit_summary(raw_text: str) -> dict:
    if not raw_text or len(raw_text.strip()) == 0:
        raise ValueError("Text cannot be empty")

    # Try LLM first, fall back to regex heuristics
    llm_result = _try_llm_parse(raw_text)
    if llm_result:
        return llm_result

    # --- Regex fallback parsing below ---
    score = 650
    customer_name = "Valued Customer"
    issues = []

    # Search for credit score pattern
    score_match = re.search(r'(?:cibil|score|rating)\s*(?:is|:|of)?\s*:?\s*\b([3-8]\d{2})\b', raw_text, re.IGNORECASE)
    if score_match:
        score = int(score_match.group(1))

    # Search for Customer Name -- Unicode-aware for Indian scripts
    name_match = re.search(r'(?:consumer\s+)?name\s*:?\s*([^\n:]{3,50})', raw_text, re.IGNORECASE)
    if name_match:
        customer_name = name_match.group(1).strip()
        customer_name = re.sub(r'\s+', ' ', customer_name)

    # Try structured account block parsing first
    raw_lines = raw_text.split('\n')
    accounts = []
    current_account = None

    for line in raw_lines:
        match = re.match(r'^\s*ACCOUNT\s*(\d+)?\s*:\s*(.+)$', line, re.IGNORECASE)
        if match:
            name = match.group(2).strip()
            if not any(name.upper().startswith(kw) for kw in ["TYPE", "STATUS", "SANCTIONED", "CURRENT", "PAYMENT", "REMARK", "BALANCE"]):
                if current_account:
                    accounts.append(current_account)
                current_account = {
                    "name": name,
                    "type": "",
                    "sanctioned_amount": "",
                    "current_balance": "",
                    "payment_status": "",
                    "remarks": "",
                    "raw_lines": [line.strip()]
                }
                continue

        if current_account:
            current_account["raw_lines"].append(line.strip())
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.upper().strip()
                val = val.strip()
                if "TYPE" in key:
                    current_account["type"] = val
                elif "SANCTIONED" in key:
                    current_account["sanctioned_amount"] = val
                elif "BALANCE" in key:
                    current_account["current_balance"] = val
                elif "STATUS" in key:
                    current_account["payment_status"] = val
                elif "REMARK" in key:
                    current_account["remarks"] = val

    if current_account:
        accounts.append(current_account)

    def format_indian_currency(amount_val: int) -> str:
        s = str(amount_val)
        if len(s) <= 3:
            return "\u20b9" + s
        last_three = s[-3:]
        remaining = s[:-3]
        out = []
        while len(remaining) > 2:
            out.append(remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            out.append(remaining)
        out.reverse()
        return "\u20b9" + ",".join(out) + "," + last_three

    for account in accounts:
        status_desc = (account["remarks"] or account["payment_status"] or "").strip()
        remarks_upper = account["remarks"].upper()
        status_upper = account["payment_status"].upper()

        is_negative = any(kw in remarks_upper or kw in status_upper for kw in ["WRITTEN OFF", "WRITTEN-OFF", "WRITE OFF", "WRITE-OFF", "SETTLED", "SETTLEMENT", "LOSS"])
        is_late = any(kw in remarks_upper or kw in status_upper for kw in ["LATE PAYMENT", "DELAYED", "OVERDUE", "DPD", "DAYS PAST DUE"])

        if is_negative or is_late:
            amount_str = ""
            for val in [account["current_balance"], account["sanctioned_amount"]]:
                if val:
                    num_match = re.search(r'([\d,]+)', val)
                    if num_match:
                        amount_str = num_match.group(1)
                        break

            amount_val = 0
            if amount_str:
                clean_digits = re.sub(r'[^\d]', '', amount_str)
                if clean_digits:
                    amount_val = int(clean_digits)

            raw_name = account["name"]
            acronyms = {"HDFC", "SBI", "ICICI", "HSBC", "PNB", "BOB", "AXIS"}
            words = []
            for w in raw_name.split():
                w_upper = w.upper()
                if w_upper in acronyms:
                    words.append(w_upper)
                else:
                    words.append(w.capitalize())
            account_title = " ".join(words)

            amount_display = format_indian_currency(amount_val) if amount_val > 0 else ""

            if is_negative:
                issue_type = "Red"
                impact = "High"
                action = "Initiate settlement negotiation or request No Objection Certificate (NOC) / Settlement letter."
                if amount_display:
                    action = f"Pay the outstanding {amount_display} or settle with the bank to obtain a clean No Objection Certificate (NOC)."

                if "SETTLE" in status_desc.upper():
                    details = f"Account settled with negative remark '{status_desc}'"
                    if amount_display:
                        details += f" and an outstanding of {amount_display}"
                    details += ". This negatively impacts your credit rating."
                else:
                    details = f"Written Off / Default status '{status_desc}'"
                    if amount_display:
                        details += f" of {amount_display}"
                    details += " observed. This severely blocks new loan approvals."
            else:
                issue_type = "Yellow"
                impact = "Medium"
                action = "Pay all overdue amounts immediately. Establish auto-debit to prevent future delays."
                details = f"Overdue payment history: {status_desc}."
                if amount_display:
                    details = f"Overdue payment history of {amount_display}: {status_desc}."

            issues.append({
                "account": account_title,
                "type": issue_type,
                "details": details[:150],
                "action": action,
                "impact": impact
            })

    # Fallback to line-by-line parsing if no accounts were structured or no issues were found
    if not issues:
        for line in raw_lines:
            if any(kw in line.upper() for kw in ["WRITTEN OFF", "WRITTEN-OFF", "WRITE OFF", "WRITE-OFF", "SETTLED", "SETTLEMENT"]):
                issues.append({
                    "account": "Active/Closed Account (from Report)",
                    "type": "Red",
                    "details": f"Negative status found: {line.strip()[:100]}",
                    "action": "Initiate settlement negotiation or request No Objection Certificate (NOC) / Settlement letter.",
                    "impact": "High"
                })
            elif any(kw in line.upper() for kw in ["LATE PAYMENT", "DELAYED", "OVERDUE", "DPD", "DAYS PAST DUE"]):
                if len(issues) < 4:
                    issues.append({
                        "account": "Active Loan/Card (from Report)",
                        "type": "Yellow",
                        "details": f"Overdue payment history: {line.strip()[:100]}",
                        "action": "Pay all overdue amounts immediately. Establish auto-debit to prevent future delays.",
                        "impact": "Medium"
                    })

    # If no issues found via regex, return empty issues (DO NOT fabricate issues)
    if not issues:
        issues = []

    # General Health description
    if score >= 750:
        general_health = "Excellent (Low Risk)"
    elif score >= 700:
        general_health = "Good (Satisfactory)"
    elif score >= 620:
        general_health = "Needs Attention (Medium Risk)"
    else:
        general_health = "Poor / Defaulted (High Risk)"

    # Action steps -- preserve order, deduplicate
    action_steps = []
    for issue in issues:
        if issue["action"] not in action_steps:
            action_steps.append(issue["action"])

    action_steps.append("Check active CIBIL report quarterly to monitor correction updates.")
    action_steps.append("Avoid making multiple new credit applications within short time windows.")

    timeline = [
        {"phase": "Month 1", "task": "Contact bank(s) to settle outstanding defaults or pay card utilization down.", "status": "Critical"},
        {"phase": "Month 2-3", "task": "Obtain No Objection Certificate (NOC) and verify bank reports status to CIBIL.", "status": "In Progress"},
        {"phase": "Month 6", "task": "Verify CIBIL score refresh and request new credit report.", "status": "Target"}
    ]

    return {
        "score": score,
        "customer_name": customer_name,
        "general_health": general_health,
        "issues": issues,
        "action_steps": action_steps,
        "timeline": timeline
    }
