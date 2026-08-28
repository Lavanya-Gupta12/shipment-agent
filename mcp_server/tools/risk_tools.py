"""
This is the deterministic safety layer, deliberately NOT left to the
LLM's judgment. Given a feasibility check result and whether customs
is involved, it computes a risk tier with plain if/else rules. The
agent must call this and respect the tier — it cannot auto-resolve a
HIGH risk case, only escalate it. This is the "LLM recommends,
software validates" pattern.
"""

import re


def assess_risk_level(feasibility_result: str, customs_flagged: bool) -> str:
    """
    Compute a deterministic risk tier (LOW/MEDIUM/HIGH) from a
    verify_eta_feasible result string and whether customs is involved.
    HIGH risk MUST be escalated to a human, not auto-resolved.
    """
    is_infeasible = feasibility_result.strip().upper().startswith("NOT FEASIBLE")

    if is_infeasible:
        return "HIGH: ETA is not feasible against the deadline — requires human approval before any action."

    if customs_flagged:
        return "HIGH: customs hold is involved - compliance issues always require human approval."

    spare_match = re.search(r"\((\d+)\s*days to spare\)", feasibility_result)
    days_spare = int(spare_match.group(1)) if spare_match else None

    if days_spare is not None and days_spare <= 1:
        return f"MEDIUM: only {days_spare} day(s) of buffer - proceed but flag for close monitoring."

    return "LOW: plan is feasible with healthy buffer — safe to auto-resolve."
