from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str = ""


def validate_user_query(query: str, max_chars: int = 400) -> GuardrailResult:
    cleaned = query.strip()
    if not cleaned:
        return GuardrailResult(False, "Query cannot be empty.")
    if len(cleaned) > max_chars:
        return GuardrailResult(False, f"Query is too long (>{max_chars} chars).")

    blocked_terms = ["hurt", "abuse", "poison", "illegal"]
    lowered = cleaned.lower()
    if any(term in lowered for term in blocked_terms):
        return GuardrailResult(False, "Unsafe request detected.")

    return GuardrailResult(True)
