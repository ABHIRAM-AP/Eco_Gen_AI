# collectors/carbon_api.py
import requests
import os

WATT_TIME_TOKEN = os.getenv("WATT_TIME_TOKEN")  # set in your env

def _get_uk_intensity(region: str) -> float | None:
    try:
        resp = requests.get(f"https://api.carbonintensity.org.uk/regional/{region}", timeout=5)
        resp.raise_for_status()
        return resp.json()["data"][0]["intensity"]["actual"]
    except Exception:
        return None

def _get_watttime_intensity(region: str) -> float | None:
    try:
        headers = {"Authorization": f"Bearer {WATT_TIME_TOKEN}"}
        resp = requests.get(
            f"https://api.watttime.org/v3/signal-index?region={region}",
            headers=headers, timeout=5
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("value")
    except Exception:
        return None

def get_carbon_intensity(region: str) -> float | None:
    """Try UK API first (free), fall back to WattTime (broader coverage)."""
    value = _get_uk_intensity(region)
    if value is not None:
        return value
    return _get_watttime_intensity(region)