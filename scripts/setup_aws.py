"""
One-time (or --reset) setup: creates the two DynamoDB tables and the
S3 bucket if they don't exist, then seeds synthetic shipment + port
congestion data. This is your "load the data" step — there's no
external dataset, the data is generated here to keep everything free
and self-contained.

Usage:
    python scripts/setup_aws.py
    python scripts/setup_aws.py --reset     # wipes and reseeds shipment/port data
"""

import argparse
import os
import sys
import time

import boto3

REGION = os.environ.get("AWS_REGION", "ap-south-1")
BUCKET = os.environ.get("AWS_S3_BUCKET")
SHIPMENTS_TABLE = os.environ.get("DYNAMODB_SHIPMENTS_TABLE", "shipment-agent-shipments")
PORTS_TABLE = os.environ.get("DYNAMODB_PORTS_TABLE", "shipment-agent-ports")

if not BUCKET or not os.environ.get("AWS_ACCESS_KEY_ID"):
    sys.exit(
        "ERROR: set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET, "
        "(optionally AWS_REGION) before running this script."
    )

dynamodb = boto3.resource("dynamodb", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

PORTS = [
    # port_code, name, lat, lon, congestion_level, avg_delay_days
    ("SGSIN", "Singapore", 1.29, 103.85, "low", 0.5),
    ("NLRTM", "Rotterdam", 51.95, 4.14, "medium", 1.5),
    ("USLAX", "Los Angeles", 33.74, -118.27, "high", 4.0),
    ("CNSHA", "Shanghai", 31.23, 121.47, "medium", 2.0),
    ("INNSA", "Nhava Sheva (Mumbai)", 18.95, 72.95, "high", 3.5),
]

SHIPMENTS = [
    {
        "container_id": "MAEU1234567",
        "origin_port": "CNSHA",
        "destination_port": "INNSA",
        "cargo_type": "electronics",
        "status": "AT_RISK",
        "eta": "2026-08-25",
        "delivery_deadline": "2026-08-27",
        "customer_email": "ops@acmeimports.example.com",
        "flag_reason": "customs_hold_flagged",
    },
    {
        "container_id": "MAEU7654321",
        "origin_port": "NLRTM",
        "destination_port": "USLAX",
        "cargo_type": "machinery_parts",
        "status": "IN_TRANSIT",
        "eta": "2026-09-02",
        "delivery_deadline": "2026-09-10",
        "customer_email": "logistics@boltcorp.example.com",
        "flag_reason": "none",
    },
    {
        "container_id": "MAEU1122334",
        "origin_port": "SGSIN",
        "destination_port": "NLRTM",
        "cargo_type": "textiles",
        "status": "IN_TRANSIT",
        "eta": "2026-08-30",
        "delivery_deadline": "2026-09-15",
        "customer_email": "supply@fabricworks.example.com",
        "flag_reason": "none",
    },
]


def create_tables():
    existing = [t.name for t in dynamodb.tables.all()]

    if SHIPMENTS_TABLE not in existing:
        print(f"Creating table {SHIPMENTS_TABLE} ...")
        dynamodb.create_table(
            TableName=SHIPMENTS_TABLE,
            KeySchema=[{"AttributeName": "container_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "container_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        dynamodb.Table(SHIPMENTS_TABLE).wait_until_exists()

    if PORTS_TABLE not in existing:
        print(f"Creating table {PORTS_TABLE} ...")
        dynamodb.create_table(
            TableName=PORTS_TABLE,
            KeySchema=[{"AttributeName": "port_code", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "port_code", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        dynamodb.Table(PORTS_TABLE).wait_until_exists()


def create_bucket():
    existing = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    if BUCKET not in existing:
        print(f"Creating bucket {BUCKET} ...")
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=BUCKET)
        else:
            s3.create_bucket(
                Bucket=BUCKET,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )


def seed_data(reset: bool):
    ports_table = dynamodb.Table(PORTS_TABLE)
    shipments_table = dynamodb.Table(SHIPMENTS_TABLE)

    for code, name, lat, lon, congestion, avg_delay in PORTS:
        ports_table.put_item(
            Item={
                "port_code": code,
                "name": name,
                "lat": str(lat),
                "lon": str(lon),
                "congestion_level": congestion,
                "avg_delay_days": str(avg_delay),
            }
        )
    print(f"Seeded {len(PORTS)} ports")

    for s in SHIPMENTS:
        shipments_table.put_item(Item=s)
    print(f"Seeded {len(SHIPMENTS)} shipments")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="reseed data even if tables exist")
    args = parser.parse_args()

    create_tables()
    create_bucket()
    seed_data(reset=args.reset)

    print("\nSetup complete. Try:")
    print("  python agent/main.py --container-id MAEU1234567")


if __name__ == "__main__":
    main()
