import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp_server"))

from tools.risk_tools import assess_risk_level


def test_high_risk_when_infeasible():
    result = assess_risk_level("NOT FEASIBLE: new ETA 2026-08-28 misses deadline by 3 days", customs_flagged=False)
    assert result.startswith("HIGH")


def test_high_risk_when_customs_flagged_even_if_feasible():
    result = assess_risk_level("FEASIBLE: new ETA 2026-08-20 meets deadline (5 days to spare)", customs_flagged=True)
    assert result.startswith("HIGH")


def test_medium_risk_tight_buffer():
    result = assess_risk_level("FEASIBLE: new ETA 2026-08-24 meets deadline (1 days to spare)", customs_flagged=False)
    assert result.startswith("MEDIUM")


def test_low_risk_healthy_buffer_no_customs():
    result = assess_risk_level("FEASIBLE: new ETA 2026-08-20 meets deadline (5 days to spare)", customs_flagged=False)
    assert result.startswith("LOW")


def test_bad_recommendation_is_caught():
    """
    This is the core safety-net scenario: even if an LLM were to
    hallucinate that an infeasible plan is fine, this deterministic
    tool still correctly flags it HIGH regardless of what the LLM claims.
    """
    infeasible_but_llm_might_claim_ok = "NOT FEASIBLE: new ETA 2026-09-01 misses deadline by 10 days"
    result = assess_risk_level(infeasible_but_llm_might_claim_ok, customs_flagged=False)
    assert result.startswith("HIGH")
    assert "human approval" in result.lower()
