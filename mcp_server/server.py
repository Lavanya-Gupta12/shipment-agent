"""
MCP server exposing shipment-exception diagnostic/resolution tools
over stdio transport. Run with: python mcp_server/server.py
(the agent launches this automatically — you don't need to run it separately)
"""

import os
import sys

# repo root must be on sys.path so `from core import ...` works inside tools/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp.server.fastmcp import FastMCP

from tools import (
    shipment_tools,
    port_tools,
    weather_tools,
    customs_tools,
    routing_tools,
    notify_tools,
    risk_tools,
)

mcp = FastMCP("shipment-exception-agent")


@mcp.tool()
def get_shipment_details(container_id: str) -> str:
    """Get full details of a shipment: origin/destination ports, status, ETA, deadline, flags."""
    return shipment_tools.get_shipment_details(container_id)


@mcp.tool()
def check_port_congestion(port_code: str) -> str:
    """Check current congestion level and average delay at a port (e.g. 'INNSA', 'USLAX')."""
    return port_tools.check_port_congestion(port_code)


@mcp.tool()
def check_weather(port_code: str) -> str:
    """Get real current weather conditions at a port to assess weather-related delay risk."""
    return weather_tools.check_weather(port_code)


@mcp.tool()
def check_customs_status(container_id: str) -> str:
    """Check whether a shipment is flagged for customs hold or inspection."""
    return customs_tools.check_customs_status(container_id)


@mcp.tool()
def propose_reroute(destination_port: str, reason: str) -> str:
    """Get alternate routing/handling options for a delayed shipment given the diagnosed reason."""
    return routing_tools.propose_reroute(destination_port, reason)


@mcp.tool()
def verify_eta_feasible(new_eta: str, delivery_deadline: str) -> str:
    """Verify a proposed new ETA (YYYY-MM-DD) still meets the delivery deadline (YYYY-MM-DD). Call this before committing any plan."""
    return routing_tools.verify_eta_feasible(new_eta, delivery_deadline)


@mcp.tool()
def assess_risk_level(feasibility_result: str, customs_flagged: bool) -> str:
    """
    REQUIRED after verify_eta_feasible: deterministically compute the risk tier
    (LOW/MEDIUM/HIGH). HIGH risk cases MUST be escalated to a human (set
    new_status to 'PENDING_HUMAN_APPROVAL'), not auto-resolved.
    """
    return risk_tools.assess_risk_level(feasibility_result, customs_flagged)


@mcp.tool()
def update_shipment_status(container_id: str, new_status: str, new_eta: str, resolution_notes: str) -> str:
    """REQUIRED before finishing: commit the final decision to DynamoDB. Use status 'PENDING_HUMAN_APPROVAL' for HIGH risk cases, 'RESOLVED' otherwise."""
    return shipment_tools.update_shipment_status(container_id, new_status, new_eta, resolution_notes)


@mcp.tool()
def draft_customer_notification(container_id: str, customer_email: str, message: str) -> str:
    """REQUIRED before finishing: draft and store the customer notification in S3."""
    return notify_tools.draft_customer_notification(container_id, customer_email, message)


if __name__ == "__main__":
    mcp.run(transport="stdio")
