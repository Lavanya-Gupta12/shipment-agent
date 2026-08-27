"""
Shared S3 layer. Object storage is used here for write-once,
human-readable artifacts (notifications, resolution audit records) —
distinct from DynamoDB, which holds the rapidly-changing live
shipment state. That separation (object store for static/historical
records vs NoSQL for live mutable state) is intentional.
"""

import datetime
import io
import os

import boto3

REGION = os.environ.get("AWS_REGION", "ap-south-1")
BUCKET = os.environ.get("AWS_S3_BUCKET")

_s3 = boto3.client("s3", region_name=REGION)


def upload_notification(container_id: str, customer_email: str, message: str) -> str:
    if not BUCKET:
        raise RuntimeError("AWS_S3_BUCKET is not set — this is required, not optional.")
    key = f"notifications/{container_id}_{datetime.datetime.utcnow().isoformat()}.txt"
    body = f"To: {customer_email}\nContainer: {container_id}\n\n{message}"
    _s3.upload_fileobj(io.BytesIO(body.encode("utf-8")), BUCKET, key)
    return key
