from core import db


def check_port_congestion(port_code: str) -> str:
    """Look up current congestion level and average delay for a port code, e.g. 'INNSA'."""
    item = db.get_port(port_code)
    if not item:
        return f"No congestion data for port {port_code}"
    return (
        f"{item['name']} ({port_code}): congestion={item['congestion_level']}, "
        f"avg_delay_days={item['avg_delay_days']}"
    )


def get_port_coords(port_code: str):
    """Internal helper used by weather_tools — not exposed as an MCP tool itself."""
    item = db.get_port(port_code)
    if not item:
        return None
    return float(item["lat"]), float(item["lon"])
