# ADR-002: LLM-First Parsing with Regex Fallback

## Status: Accepted

## Date: 2026-05-21

## Context

Credit report parsing is the core value proposition. The initial implementation used only regex heuristics, which:
- Failed on non-standard report formats
- Produced false positives (matching dates/amounts as scores)
- Could not understand context or nuance
- Generated fabricated issues when no patterns matched

## Decision

Implement a two-tier parsing strategy:

1. **Primary: LLM (OpenAI gpt-4o-mini)** -- Structured JSON prompt with strict schema validation
2. **Fallback: Regex heuristics** -- Only when LLM is unavailable (no API key, API failure)

The LLM prompt enforces:
- Score range validation (300-900)
- No fabricated issues (empty array if none found)
- Title case for account names with acronym preservation
- Maximum 5 action steps, 2-4 timeline phases
- Output ONLY valid JSON

## Consequences

**Positive:**
- Handles any credit bureau format (CIBIL, Experian, Equifax, CRIF)
- No fabricated data ever reaches the user
- Graceful degradation when LLM is unavailable
- Structured output eliminates parsing bugs

**Negative:**
- LLM latency adds 2-5 seconds to report processing
- API cost per report (~$0.002 per report with gpt-4o-mini)
- Requires internet connectivity for primary path

## Alternatives Considered

- **Regex only:** Rejected -- too brittle, produces fake data
- **Fine-tuned model:** Rejected -- too expensive for MVP, requires training data
- **Human-in-the-loop:** Rejected -- doesn't scale, defeats purpose of automation
- **Third-party credit parsing API:** Rejected -- no Indian bureau-specific APIs available
