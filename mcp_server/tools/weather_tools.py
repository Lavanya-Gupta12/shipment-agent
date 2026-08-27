"""
Real live weather data from Open-Meteo (https://open-meteo.com) — free,
no API key required, no rate-limit issues for demo-scale use. This is
the one tool in the project that hits a genuine external API rather
than mock/seeded data.
"""

import requests

from . import port_tools


def check_weather(port_code: str) -> str:
    """Get current weather conditions at a port, to assess weather-related delay risk."""
    coords = port_tools.get_port_coords(port_code)
    if coords is None:
        return f"Unknown port code {port_code}, cannot fetch weather"
    lat, lon = coords

    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,precipitation",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json().get("current", {})
    wind = data.get("wind_speed_10m")
    precip = data.get("precipitation")
    temp = data.get("temperature_2m")

    risk = "low"
    if wind is not None and wind > 40:
        risk = "high (strong winds)"
    elif precip is not None and precip > 5:
        risk = "medium (heavy precipitation)"

    return (
        f"Weather at {port_code}: temp={temp}C, wind={wind}km/h, "
        f"precipitation={precip}mm, delay_risk={risk}"
    )
