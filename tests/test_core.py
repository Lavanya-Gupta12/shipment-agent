"""
Uses moto (free, open-source) to mock DynamoDB and S3 so these tests
run with no real AWS account or cost. This is what CI runs.
"""

import os
import sys

import boto3
import pytest
from moto import mock_aws

os.environ.setdefault("AWS_REGION", "ap-south-1")
os.environ.setdefault("AWS_S3_BUCKET", "test-bucket")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def aws():
    with mock_aws():
        region = os.environ["AWS_REGION"]
        dynamodb = boto3.resource("dynamodb", region_name=region)
        dynamodb.create_table(
            TableName="shipment-agent-shipments",
            KeySchema=[{"AttributeName": "container_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "container_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        dynamodb.create_table(
            TableName="shipment-agent-ports",
            KeySchema=[{"AttributeName": "port_code", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "port_code", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        s3 = boto3.client("s3", region_name=region)
        s3.create_bucket(
            Bucket=os.environ["AWS_S3_BUCKET"],
            CreateBucketConfiguration={"LocationConstraint": region},
        )
        yield


def test_create_and_get_shipment(aws):
    from core import db
    item = db.create_shipment({
        "container_id": "TEST0001",
        "origin_port": "CNSHA",
        "destination_port": "INNSA",
        "eta": "2026-08-25",
        "delivery_deadline": "2026-08-27",
        "customer_email": "test@example.com",
    })
    assert item["status"] == "NEW"

    fetched = db.get_shipment("TEST0001")
    assert fetched["container_id"] == "TEST0001"


def test_update_shipment_status(aws):
    from core import db
    db.create_shipment({"container_id": "TEST0002", "eta": "2026-08-25"})
    updated = db.update_shipment("TEST0002", "RESOLVED", "2026-08-26", "Rerouted via Colombo")
    assert updated["status"] == "RESOLVED"
    assert updated["eta"] == "2026-08-26"
    assert updated["resolution_notes"] == "Rerouted via Colombo"


def test_get_nonexistent_shipment_returns_none(aws):
    from core import db
    assert db.get_shipment("DOES_NOT_EXIST") is None


def test_upload_notification(aws):
    from core import storage
    key = storage.upload_notification("TEST0001", "test@example.com", "Your shipment is delayed.")
    assert key.startswith("notifications/TEST0001_")
