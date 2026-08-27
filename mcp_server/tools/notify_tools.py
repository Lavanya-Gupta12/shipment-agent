"""
Drafts a customer-facing notification and uploads it to S3 as the
audit record. This is a REQUIRED step — the agent's system prompt
and agent/main.py both enforce that a run cannot finish successfully
without this succeeding.
"""

from core import storage


def draft_customer_notification(container_id: str, customer_email: str, message: str) -> str:
    """Draft a customer notification about the shipment exception and store it in S3 as an audit record."""
    key = storage.upload_notification(container_id, customer_email, message)
    return f"Notification drafted and stored at s3://{storage.BUCKET}/{key}"
