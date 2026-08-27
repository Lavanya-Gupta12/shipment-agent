import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))

from state import AgentState


def test_called_detects_successful_update():
    state = AgentState()
    state.record("update_shipment_status", {}, "reasoning", "Updated MAEU1234567 in DynamoDB: status=RESOLVED")
    assert state.called("update_shipment_status", "Updated") is True


def test_called_returns_false_when_never_called():
    state = AgentState()
    assert state.called("update_shipment_status", "Updated") is False


def test_called_returns_false_on_failed_call():
    state = AgentState()
    state.record("update_shipment_status", {}, "reasoning", "ERROR calling update_shipment_status: timeout")
    assert state.called("update_shipment_status", "Updated") is False


def test_history_accumulates_in_order():
    state = AgentState()
    state.record("get_shipment_details", {"container_id": "X"}, "start", "some details")
    state.record("check_customs_status", {"container_id": "X"}, "diagnose", "no issues")
    assert len(state.history) == 2
    assert state.history[0]["action"] == "get_shipment_details"
    assert state.history[1]["action"] == "check_customs_status"
