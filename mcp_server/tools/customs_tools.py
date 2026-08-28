"""
Real customs status APIs require paid/private access, so this is a
deterministic mock: it reads the shipment's seeded flag_reason from
DynamoDB (set by scripts/setup_aws.py or POST /shipments) rather than
random data, so results are reproducible for demos and tests.
"""

from core import db


def check_customs_status(container_id: str) -> str:
    """Check whether a shipment is flagged for customs hold or inspection."""
    item = db.get_shipment(container_id)
    if not item:
        return f"No shipment found with container_id {container_id}"
    flag = item.get("flag_reason", "none")
    if flag == "customs_hold_flagged":
        return f"{container_id}: CUSTOMS HOLD - flagged for documentation review at destination port"
    return f"{container_id}: no customs issues, cleared"
