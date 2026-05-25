"""
CLYR v2 — LLM Service
Analyzes credit report text and generates personalized recovery letters.
Supports 11 Indian languages with proper vernacular tone.
Includes retry logic, caching, and fallback.
"""
import os
import re
import json
import hashlib
import logging
import time
from functools import lru_cache
from openai import OpenAI, APIError, RateLimitError

from app.config import config

logger = logging.getLogger(__name__)

# OpenRouter client — lazy initialization to avoid crash when API key is missing
_client = None

def get_client():
    """Get or create the OpenAI client (lazy init)."""
    global _client
    if _client is None:
        api_key = config.openai_api_key
        if not api_key:
            logger.warning("OPENAI_API_KEY not set — LLM features will use fallback")
            return None
        _client = OpenAI(
            base_url=config.openai_base_url,
            api_key=api_key,
        )
    return _client

# In-memory cache
_llm_cache: dict[str, dict] = {}
_CACHE_MAX_SIZE = 100
_CACHE_TTL = 3600  # 1 hour


def _get_cache_key(text: str, language: str) -> str:
    """Generate cache key from text + language."""
    return hashlib.sha256(f"{text[:8000]}:{language}".encode()).hexdigest()


def _get_cached(key: str) -> dict | None:
    """Get cached result if not expired."""
    if key in _llm_cache:
        entry = _llm_cache[key]
        if time.time() - entry["timestamp"] < _CACHE_TTL:
            return entry["data"]
        else:
            del _llm_cache[key]
    return None


def _set_cache(key: str, data: dict):
    """Cache result with LRU eviction."""
    if len(_llm_cache) >= _CACHE_MAX_SIZE:
        # Remove oldest entry
        oldest_key = min(_llm_cache, key=lambda k: _llm_cache[k]["timestamp"])
        del _llm_cache[oldest_key]
    _llm_cache[key] = {"data": data, "timestamp": time.time()}


# Language-specific tone instructions
LANGUAGE_INSTRUCTIONS = {
    "en": "Write in plain, friendly English. Use a 'friend over chai' tone. No jargon.",
    "hi": "हिंग्लिश में लिखें। दोस्ताना टोन रखें। बैंक की भाषा मत इस्तेमाल करें। आसान शब्दों में समझाएं।",
    "bn": "সহজ বাংলায় লিখুন। বন্ধুর মতো কথা বলুন। ব্যাংকের ভাষা ব্যবহার করবেন না।",
    "te": "సులభమైన తెలుగులో వ్రాయండి. స్నేహితుడిగా మాట్లాడండి.",
    "mr": "सोप्या मराठीत लिहा. मित्रासारखे बोला. बँकेची भाषा वारू नका.",
    "ta": "எளிதான தமிழில் எழுதுங்கள். நண்பரை போல பேசுங்கள்.",
    "gu": "સરળ ગુજરાતીમાં લખો. મિત્ર જેવો ટોન રાખો.",
    "kn": "ಸರಳ ಕನ್ನಡದಲ್ಲಿ ಬರೆಯಿರಿ. ಗೆಳೆಯಂದೆ ಮಾತಾಡಿ.",
    "ml": "ലളിതമായ മലയാളത്തിൽ എഴുതുക. സുഹൃത്തിനെ പോലെ സംസാരിക്കുക.",
    "pa": "ਆਸਾਨ ਪੰਜਾਬੀ ਵਿੱਚ ਲਿਖੋ। ਦੋਸਤ ਵਰਗਾ ਟੋਨ ਰੱਖੋ।",
}

SYSTEM_PROMPT = """You are CLYR — an expert credit advisor for Indian consumers. You analyze CIBIL/credit reports 
and produce personalized recovery letters. Your tone is warm, direct, and jargon-free — like a smart friend 
who works in banking explaining things over chai.

CRITICAL RULES:
1. NEVER make up numbers or accounts not present in the report
2. If you can't find specific information, say so honestly
3. Every issue MUST have a concrete, actionable step
4. Score projections must be realistic (max +100 points from fixes)
5. Always include a dispute letter for incorrect entries
6. Output MUST follow the exact format specified below

OUTPUT FORMAT (strict — follow exactly):
```
GREETING: [Person's name with respectful address]

INTRODUCTION paragraph: 2-3 sentences. Current score, overall health, reassurance.

ISSUE #1: [Account Name] — [Type: Red/Yellow]
WHAT: [What's wrong — specific numbers, dates from report]
IMPACT: [Score impact in points]
ACTION: [Step-by-step what to do — numbered list]
TIMELINE: [How long to fix]
SUCCESS_CHANCE: [High/Medium/Low]

ISSUE #2: ...

SCORE_PROJECTION:
Current: [score]
After fixing: [realistic projected score + range]
Timeline: [months]

CLOSING: Encouraging paragraph — 2-3 sentences

DISPUTE_LETTERS:
[For each incorrect/inaccurate entry, provide a ready-to-send formal dispute letter]
```"""


def _build_user_prompt(raw_text: str, language: str) -> str:
    """Build the user prompt with report text and language instructions."""
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])
    return f"""Analyze this credit report and produce a personalized recovery letter.

LANGUAGE INSTRUCTION: {lang_instruction}

CREDIT REPORT TEXT:
{raw_text[:15000]}

Now produce the complete analysis following the exact output format."""


def _parse_llm_output(output: str) -> dict:
    """Parse the structured LLM output into a dict."""
    result = {
        "customer_name": "",
        "score": 0,
        "general_health": "",
        "letter": output,  # Full letter text for PDF generation
        "issues": [],
        "action_steps": [],
        "timeline": [],
    }

    # Extract customer name from greeting
    greeting_match = re.search(r"GREETING:\s*(.+)", output)
    if greeting_match:
        name_line = greeting_match.group(1).strip()
        # Remove "Dear" and commas
        name = re.sub(r"^(Dear|Respected|Namaste)\s*", "", name_line, flags=re.IGNORECASE)
        name = name.rstrip(",").strip()
        result["customer_name"] = name

    # Extract score from intro
    score_match = re.search(r"score is (\d{3})", output, re.IGNORECASE)
    if not score_match:
        score_match = re.search(r"स्कोर (\d{3})", output)
    if score_match:
        result["score"] = int(score_match.group(1))

    # Extract health summary
    health_match = re.search(r"score is \d+\s*[—–-]\s*(.+?)(?:\.|$)", output)
    if health_match:
        result["general_health"] = health_match.group(1).strip()

    # Extract issues
    issue_blocks = re.split(r"ISSUE #\d+:", output)[1:]  # Skip before first issue
    for block in issue_blocks:
        issue = {"account": "", "type": "Yellow", "details": "", "impact": "", "action": ""}
        
        # Account name (first line after ISSUE #)
        lines = block.strip().split("\n")
        if lines:
            header = lines[0].strip()
            # "HDFC Credit Card — Red" or "SBI Loan — Yellow"
            parts = re.split(r"\s*[—–-]\s*", header)
            if len(parts) >= 2:
                issue["account"] = parts[0].strip()
                issue["type"] = parts[1].strip()
            else:
                issue["account"] = header

        # WHAT:
        what_match = re.search(r"WHAT:\s*(.+?)(?=IMPACT:|ACTION:|TIMELINE:|$)", block, re.DOTALL)
        if what_match:
            issue["details"] = what_match.group(1).strip()

        # IMPACT:
        impact_match = re.search(r"IMPACT:\s*(.+?)(?=ACTION:|TIMELINE:|$)", block, re.DOTALL)
        if impact_match:
            issue["impact"] = impact_match.group(1).strip()

        # ACTION:
        action_match = re.search(r"ACTION:\s*(.+?)(?=TIMELINE:|SUCCESS_CHANCE:|$)", block, re.DOTALL)
        if action_match:
            action_text = action_match.group(1).strip()
            issue["action"] = action_text
            # Add to action steps (numbered steps)
            steps = [s.strip() for s in re.split(r"[\d]+\.|\n-", action_text) if s.strip()]
            result["action_steps"].extend(steps)

        if issue["account"]:
            result["issues"].append(issue)

    # Extract timeline items from action steps projection
    timeline_section = re.search(
        r"TIMELINE:\s*(.+?)(?=SUCCESS_CHANCE:|SCORE_PROJECTION:|CLOSING:|$)",
        output, re.DOTALL
    )
    if timeline_section:
        timeline_text = timeline_section.group(1).strip()
        for line in timeline_text.split("\n"):
            line = line.strip()
            if ":" in line and line:
                phase, task = line.split(":", 1)
                result["timeline"].append({
                    "phase": phase.strip(),
                    "task": task.strip(),
                    "status": "Pending"
                })

    # If no structured timeline, generate one from issues
    if not result["timeline"] and result["issues"]:
        for i, issue in enumerate(result["issues"], 1):
            result["timeline"].append({
                "phase": f"Month {i}",
                "task": f"Resolve: {issue['account']}",
                "status": "Pending"
            })

    return result


def generate_credit_summary(raw_text: str, language: str = "en") -> dict:
    """
    Analyze a credit report using LLM.
    
    Args:
        raw_text: Extracted text from the credit report PDF
        language: Language code (en, hi, bn, te, mr, ta, gu, kn, ml, pa)
    
    Returns:
        Dict with score, issues, action_steps, timeline, letter, etc.
    
    Raises:
        ValueError: If raw_text is empty or LLM fails after retries
    """
    if not raw_text or len(raw_text.strip()) < 50:
        raise ValueError("Credit report text is too empty or too short. Make sure the PDF has readable text.")

    # Check cache
    cache_key = _get_cache_key(raw_text, language)
    cached = _get_cached(cache_key)
    if cached:
        logger.info("LLM cache hit for key %s...", cache_key[:8])
        return cached

    # Try LLM with retries
    last_error = None
    client = get_client()
    if client is None:
        logger.warning("No LLM client available — using regex fallback")
        return _regex_fallback(raw_text, language)
    for attempt in range(3):
        try:
            logger.info("LLM call attempt %d/3 for language=%s", attempt + 1, language)
            
            response = client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(raw_text, language)},
                ],
                max_tokens=4000,
                temperature=0.3,
                timeout=60,
            )

            output = response.choices[0].message.content
            if not output:
                raise ValueError("LLM returned empty response")

            result = _parse_llm_output(output)
            result["language"] = language
            result["score"] = result["score"] or 600  # Default if not found
            
            # Validate result
            if not result["issues"]:
                logger.warning("LLM found no issues, using fallback parsing")
                result = _fallback_parsing(raw_text, result)

            # Cache the result
            _set_cache(cache_key, result)
            
            logger.info("LLM analysis complete: score=%s, issues=%d", result["score"], len(result["issues"]))
            return result

        except RateLimitError:
            last_error = "Rate limited by LLM provider"
            wait_time = (attempt + 1) * 5
            logger.warning("Rate limited, waiting %ds...", wait_time)
            time.sleep(wait_time)
        except APIError as e:
            last_error = f"LLM API error: {e}"
            logger.error("LLM API error (attempt %d): %s", attempt + 1, e)
            time.sleep(2)
        except Exception as e:
            last_error = f"Unexpected error: {e}"
            logger.error("LLM unexpected error (attempt %d): %s", attempt + 1, e)
            time.sleep(1)

    # All retries failed — use fallback
    logger.error("All LLM retries failed: %s. Using fallback parsing.", last_error)
    return _fallback_parsing(raw_text, {
        "customer_name": "",
        "score": 0,
        "general_health": "Needs Analysis",
        "letter": "",
        "issues": [],
        "action_steps": [],
        "timeline": [],
        "language": language,
    })


def _regex_fallback(raw_text: str, language: str) -> dict:
    """
    Fallback when LLM client is not available (no API key).
    Uses regex to extract basic info and generates a simple structured result.
    """
    import re as _re
    result = {
        "customer_name": "",
        "score": 0,
        "general_health": "Unknown",
        "letter": "",
        "issues": [],
        "action_steps": [],
        "timeline": [],
        "language": language,
    }

    # Extract name
    name_match = _re.search(r"(?:CONSUMER\s+NAME|NAME|Customer)[\s:]+([A-Za-z\s]+)", raw_text, _re.IGNORECASE)
    if name_match:
        result["customer_name"] = name_match.group(1).strip()

    # Extract score
    score_patterns = [
        r"CIBIL\s+(?:TransUnion\s+)?Score[\s:]+(\d{3})",
        r"Credit\s+Score[\s:]+(\d{3})",
        r"Score[\s:]+(\d{3})",
        r"(\d{3})\s*(?:out of|/)\s*900",
    ]
    for pat in score_patterns:
        m = _re.search(pat, raw_text, _re.IGNORECASE)
        if m:
            result["score"] = int(m.group(1))
            break
    if not result["score"]:
        result["score"] = 600

    score = result["score"]
    if score >= 750:
        result["general_health"] = "Good"
    elif score >= 650:
        result["general_health"] = "Fair"
    else:
        result["general_health"] = "Needs Attention"

    # Find issues
    negative_patterns = [
        (r"written\s+off", "Written Off Account", "Red"),
        (r"settled", "Settled Account", "Yellow"),
        (r"overdue", "Overdue Payment", "Red"),
        (r"default", "Default", "Red"),
        (r"late\s+payment", "Late Payment", "Yellow"),
    ]
    found = set()
    for pat, issue_type, severity in negative_patterns:
        if _re.search(pat, raw_text, _re.IGNORECASE):
            key = issue_type.lower()
            if key not in found:
                found.add(key)
                result["issues"].append({
                    "account": issue_type,
                    "type": severity,
                    "details": f"Detected '{issue_type}' in your credit report.",
                    "impact": "This is negatively affecting your credit score.",
                    "action": f"Contact your bank to resolve the {issue_type.lower()}. Request an NOC after payment.",
                })

    if not result["issues"]:
        result["issues"].append({
            "account": "No Major Issues Found",
            "type": "Green",
            "details": "Your report was analyzed. No specific negative entries were detected.",
            "impact": "Your score appears stable.",
            "action": "Continue making timely payments and keep credit utilization low.",
        })

    result["action_steps"] = [
        f"Contact bank to resolve: {issue['account']}" for issue in result["issues"]
        if issue["type"] != "Green"
    ]
    if not result["action_steps"]:
        result["action_steps"] = [
            "Continue making timely payments",
            "Keep credit utilization below 30%",
            "Avoid applying for multiple credit products in short succession",
        ]
    result["action_steps"].append("Check your CIBIL report again after 30 days to verify updates.")

    result["timeline"] = [
        {"phase": "Month 1", "task": "Contact banks for dispute resolution", "status": "Critical"},
        {"phase": "Month 2-3", "task": "Make overdue payments, set up auto-debit", "status": "In Progress"},
        {"phase": "Month 6", "task": "Re-check CIBIL score for improvement", "status": "Target"},
    ]

    # Generate letter
    name = result["customer_name"] or "Customer"
    letter_parts = [f"Dear {name},"]
    letter_parts.append(f"\nYour credit score is {result['score']} — {result['general_health']}.")
    letter_parts.append("\nHere's what I found:\n")
    for i, issue in enumerate(result["issues"], 1):
        letter_parts.append(f"ISSUE #{i}: {issue['account']} — {issue['type']}")
        letter_parts.append(f"WHAT: {issue['details']}")
        letter_parts.append(f"IMPACT: {issue['impact']}")
        letter_parts.append(f"ACTION: {issue['action']}\n")
    letter_parts.append("SCORE_PROJECTION:")
    letter_parts.append(f"Current: {result['score']}")
    letter_parts.append(f"After fixing: {min(900, result['score'] + 50)}-{min(900, result['score'] + 100)}")
    letter_parts.append("Timeline: 3-6 months\n")
    letter_parts.append("CLOSING: Keep at it, boss. Your score WILL improve if you follow these steps consistently.")
    result["letter"] = "\n".join(letter_parts)

    return result


def _fallback_parsing(raw_text: str, result: dict) -> dict:
    """
    Fallback parsing when LLM fails.
    Uses regex patterns to extract common credit report elements.
    """
    score_patterns = [
        r"CIBIL\s+(?:TransUnion\s+)?Score[:\s]+(\d{3})",
        r"Credit\s+Score[:\s]+(\d{3})",
        r"Score[:\s]+(\d{3})",
        r"(\d{3})\s*(?:out of|/)\s*900",
    ]
    for pattern in score_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            result["score"] = int(match.group(1))
            break

    if not result["score"]:
        result["score"] = 600  # Conservative default

    # Set health based on score
    score = result["score"]
    if score >= 750:
        result["general_health"] = "Good"
    elif score >= 650:
        result["general_health"] = "Fair"
    else:
        result["general_health"] = "Needs Attention"

    # Look for common negative patterns
    negative_patterns = [
        (r"written\s+off", "Written Off Account", "Red"),
        (r"settled", "Settled Account", "Yellow"),
        (r"overdue", "Overdue Payment", "Red"),
        (r"default", "Default", "Red"),
        (r"late\s+payment", "Late Payment", "Yellow"),
        (r"hard\s+enquir", "Hard Inquiry", "Yellow"),
    ]

    found_accounts = set()
    for pattern, issue_type, severity in negative_patterns:
        if re.search(pattern, raw_text, re.IGNORECASE):
            account_key = issue_type.lower()
            if account_key not in found_accounts:
                found_accounts.add(account_key)
                result["issues"].append({
                    "account": issue_type,
                    "type": severity,
                    "details": f"Detected '{issue_type}' pattern in your credit report.",
                    "impact": "This is negatively affecting your credit score.",
                    "action": f"Contact your bank to resolve the {issue_type.lower()}. Request an NOC after payment.",
                })

    # Generate basic action steps
    if result["issues"]:
        result["action_steps"] = [
            f"Contact bank to resolve: {issue['account']}" for issue in result["issues"]
        ]
        result["action_steps"].append("Check your CIBIL report again after 30 days to verify updates.")
        result["action_steps"].append("Keep credit card utilization below 30%.")
    else:
        result["issues"].append({
            "account": "No Major Issues Found",
            "type": "Green",
            "details": "Your report was analyzed. The LLM couldn't find specific negative entries, or the report format wasn't recognized.",
            "impact": "Your score appears stable.",
            "action": "Upload a more recent report or contact support for manual review.",
        })
        result["action_steps"] = [
            "Continue making timely payments",
            "Keep credit utilization low",
            "Avoid applying for multiple credit products in short succession",
        ]

    # Generate a simple timeline
    result["timeline"] = [
        {"phase": "Month 1", "task": "Contact banks for dispute resolution", "status": "Critical"},
        {"phase": "Month 2-3", "task": "Make overdue payments, set up auto-debit", "status": "In Progress"},
        {"phase": "Month 6", "task": "Re-check CIBIL score for improvement", "status": "Target"},
    ]

    # Generate a simple letter
    name = result["customer_name"] or "Customer"
    letter_parts = [f"Dear {name},"]
    letter_parts.append(f"\nYour credit score is {result['score']} — {result['general_health']}.")
    letter_parts.append("\nHere's what I found:\n")

    for i, issue in enumerate(result["issues"], 1):
        letter_parts.append(f"ISSUE #{i}: {issue['account']} — {issue['type']}")
        letter_parts.append(f"WHAT: {issue['details']}")
        letter_parts.append(f"IMPACT: {issue['impact']}")
        letter_parts.append(f"ACTION: {issue['action']}\n")

    letter_parts.append("\nTake it one step at a time. You've got this.")
    letter_parts.append("\n— CLYR")

    result["letter"] = "\n".join(letter_parts)

    return result
