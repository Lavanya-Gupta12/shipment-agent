"""
Thin MCP-tool wrappers around core.db. Kept separate from core so
tool docstrings (used by the LLM to decide when to call each tool)
stay focused, while the actual DynamoDB logic lives in one place.
"""

from core import db


def get_shipment_details(container_id: str) -> str:
    item = db.get_shipment(container_id)
    if not item:
        return f"No shipment found with container_id {container_id}"
    return str(item)


def update_shipment_status(container_id: str, new_status: str, new_eta: str, resolution_notes: str) -> str:
    db.update_shipment(container_id, new_status, new_eta, resolution_notes)
    return f"Updated {container_id} in DynamoDB: status={new_status}, eta={new_eta}"
