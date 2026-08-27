"""
REST API layer. Talks to the same core.db / core.storage repository
functions the MCP tools use, so there's one source of truth for
shipment state — the API isn't a separate system that duplicates logic.

Run with (from repo root):
    uvicorn api.main:app --reload
"""

import asyncio
import os
import sys

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core import db
from agent.main import run_agent

app = FastAPI(title="Shipment Exception Resolution API")


class ShipmentCreate(BaseModel):
    container_id: str
    origin_port: str
    destination_port: str
    cargo_type: str
    eta: str
    delivery_deadline: str
    customer_email: str
    flag_reason: str = "none"


class ResolveRequest(BaseModel):
    approved: bool
    notes: str = ""


@app.post("/shipments")
def create_shipment(shipment: ShipmentCreate):
    item = db.create_shipment(shipment.model_dump())
    return item


@app.get("/shipments/{container_id}")
def get_shipment(container_id: str):
    item = db.get_shipment(container_id)
    if not item:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return item


@app.get("/shipments/{container_id}/status")
def get_status(container_id: str):
    item = db.get_shipment(container_id)
    if not item:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return {
        "container_id": container_id,
        "status": item.get("status"),
        "eta": item.get("eta"),
        "resolution_notes": item.get("resolution_notes", ""),
    }


@app.post("/shipments/{container_id}/investigate")
def investigate_shipment(container_id: str):
    """Triggers the agent to investigate and (if not escalated) resolve this shipment."""
    item = db.get_shipment(container_id)
    if not item:
        raise HTTPException(status_code=404, detail="Shipment not found")

    result = asyncio.run(run_agent(container_id, verbose=False))
    return result


@app.post("/shipments/{container_id}/resolve")
def resolve_shipment(container_id: str, body: ResolveRequest):
    """
    For shipments the agent escalated (status = PENDING_HUMAN_APPROVAL).
    A human calls this to approve or reject the agent's proposed plan.
    """
    item = db.get_shipment(container_id)
    if not item:
        raise HTTPException(status_code=404, detail="Shipment not found")
    if item.get("status") != "PENDING_HUMAN_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=f"Shipment is not pending approval (current status: {item.get('status')})",
        )

    new_status = "RESOLVED" if body.approved else "REJECTED_BY_HUMAN"
    updated = db.update_shipment(
        container_id, new_status, item.get("eta", ""), body.notes or "Resolved by human reviewer"
    )
    return updated
