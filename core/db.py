"""
Shared DynamoDB repository layer. Both the MCP tool layer (used by
the agent) and the FastAPI layer (used by external callers/humans)
go through this same module, so there's one source of truth for how
shipment state is read/written — not duplicated boto3 calls in two places.
"""

import os

import boto3

REGION = os.environ.get("AWS_REGION", "ap-south-1")
SHIPMENTS_TABLE = os.environ.get("DYNAMODB_SHIPMENTS_TABLE", "shipment-agent-shipments")
PORTS_TABLE = os.environ.get("DYNAMODB_PORTS_TABLE", "shipment-agent-ports")

_dynamodb = boto3.resource("dynamodb", region_name=REGION)


def _shipments_table():
    return _dynamodb.Table(SHIPMENTS_TABLE)


def _ports_table():
    return _dynamodb.Table(PORTS_TABLE)


def get_shipment(container_id: str) -> dict | None:
    resp = _shipments_table().get_item(Key={"container_id": container_id})
    return resp.get("Item")


def create_shipment(item: dict) -> dict:
    if "container_id" not in item:
        raise ValueError("item must include container_id")
    item.setdefault("status", "NEW")
    item.setdefault("flag_reason", "none")
    _shipments_table().put_item(Item=item)
    return item


def update_shipment(container_id: str, new_status: str, new_eta: str, resolution_notes: str) -> dict:
    _shipments_table().update_item(
        Key={"container_id": container_id},
        UpdateExpression="SET #s = :s, eta = :e, resolution_notes = :n",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": new_status, ":e": new_eta, ":n": resolution_notes},
    )
    return get_shipment(container_id)


def get_port(port_code: str) -> dict | None:
    resp = _ports_table().get_item(Key={"port_code": port_code})
    return resp.get("Item")
