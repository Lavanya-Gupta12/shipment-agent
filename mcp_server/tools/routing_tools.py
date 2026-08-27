"""
propose_reroute is a small static lookup (kept simple for scope);
verify_eta_feasible is the agent's verification/feedback gate — a
proposed plan is only accepted if it fits the delivery deadline.
"""

import datetime

# small static graph of reasonable alternate routes for demo purposes
ALTERNATE_ROUTES = {
    "INNSA": [("Direct berth reassignment at INNSA", 1), ("Divert via Colombo (LKCMB)", 3)],
    "USLAX": [("Divert via Long Beach", 2), ("Hold and wait for berth", 4)],
    "NLRTM": [("Divert via Antwerp (BEANR)", 2)],
}


def propose_reroute(destination_port: str, reason: str) -> str:
    """Suggest alternate routing/handling options for a delayed shipment given the diagnosed reason."""
    options = ALTERNATE_ROUTES.get(destination_port)
    if not options:
        return f"No predefined alternate routes for {destination_port}; recommend manual review."
    lines = [f"{name} (+{extra_days}d)" for name, extra_days in options]
    return f"Proposed options for {destination_port} (reason: {reason}):\n" + "\n".join(lines)


def verify_eta_feasible(new_eta: str, delivery_deadline: str) -> str:
    """Check whether a proposed new ETA (YYYY-MM-DD) still meets the delivery deadline (YYYY-MM-DD)."""
    try:
        eta = datetime.date.fromisoformat(new_eta)
        deadline = datetime.date.fromisoformat(delivery_deadline)
    except ValueError:
        return "ERROR: dates must be in YYYY-MM-DD format"

    if eta <= deadline:
        days_to_spare = (deadline - eta).days
        return f"FEASIBLE: new ETA {new_eta} meets deadline {delivery_deadline} ({days_to_spare} days to spare)"
    days_late = (eta - deadline).days
    return f"NOT FEASIBLE: new ETA {new_eta} misses deadline {delivery_deadline} by {days_late} days — reconsider"
