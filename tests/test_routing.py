import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp_server"))

from tools.routing_tools import verify_eta_feasible, propose_reroute


def test_verify_eta_feasible_with_buffer():
    result = verify_eta_feasible("2026-08-20", "2026-08-25")
    assert result.startswith("FEASIBLE")
    assert "5 days to spare" in result


def test_verify_eta_feasible_exact_deadline():
    result = verify_eta_feasible("2026-08-25", "2026-08-25")
    assert result.startswith("FEASIBLE")
    assert "0 days to spare" in result


def test_verify_eta_feasible_missed_deadline():
    result = verify_eta_feasible("2026-08-28", "2026-08-25")
    assert result.startswith("NOT FEASIBLE")
    assert "3 days" in result


def test_verify_eta_feasible_bad_date_format():
    result = verify_eta_feasible("not-a-date", "2026-08-25")
    assert "ERROR" in result


def test_propose_reroute_known_port():
    result = propose_reroute("INNSA", "customs_hold_flagged")
    assert "INNSA" in result
    assert "Colombo" in result or "berth" in result.lower()


def test_propose_reroute_unknown_port():
    result = propose_reroute("ZZZZZ", "unknown_reason")
    assert "No predefined alternate routes" in result
