# collectors/carbon_api.py
import os
import requests
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

_WATTTIME_TOKEN_CACHE: str | None = os.getenv("WATT_TIME_TOKEN")

# Fallback regional carbon intensities (gCO2eq / kWh) in case of network timeout
REGIONAL_FALLBACK_CI: dict[str, float] = {
    "US-CAL-CISO": 385.0,
    "CAISO_NORTH": 385.0,
    "US-EAST": 420.0,
    "UK": 175.0,
    "EU-CENTRAL": 290.0,
    "IN": 710.0,
}


def _get_uk_intensity(region: str) -> float | None:
    norm = region.strip().lower()
    try:
        if norm in ("uk", "gb", "great britain", "england", "scotland", "wales"):
            resp = requests.get("https://api.carbonintensity.org.uk/intensity", timeout=1.5)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if data and "intensity" in data[0]:
                actual = data[0]["intensity"].get("actual")
                forecast = data[0]["intensity"].get("forecast")
                return float(actual if actual is not None else forecast)
        resp = requests.get(f"https://api.carbonintensity.org.uk/regional/{region}", timeout=1.5)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if data and "intensity" in data[0]:
            return float(data[0]["intensity"].get("actual") or data[0]["intensity"].get("forecast") or 0.0)
    except Exception:
        return None
    return None


def _get_watttime_token() -> str | None:
    global _WATTTIME_TOKEN_CACHE
    if _WATTTIME_TOKEN_CACHE:
        return _WATTTIME_TOKEN_CACHE

    user = os.getenv("WATTTIME_USER")
    pwd = os.getenv("WATTTIME_PASS")
    if user and pwd:
        try:
            resp = requests.get("https://api.watttime.org/login", auth=(user, pwd), timeout=1.5)
            if resp.status_code == 200:
                token = resp.json().get("token")
                if token:
                    _WATTTIME_TOKEN_CACHE = token
                    return token
        except Exception:
            pass
    return None


def _get_watttime_intensity(region: str) -> float | None:
    token = _get_watttime_token()
    if not token:
        return None

    # Map standard region aliases to WattTime supported balancing authorities
    region_map = {
        "US-CAL-CISO": "CAISO_NORTH",
        "CAISO": "CAISO_NORTH",
    }
    target_region = region_map.get(region, region)

    headers = {"Authorization": f"Bearer {token}"}
    try:
        # Request forecast/live MOER (lbs CO2 / MWh)
        resp = requests.get(
            f"https://api.watttime.org/v3/forecast?region={target_region}&signal_type=co2_moer",
            headers=headers,
            timeout=1.5,
        )
        if resp.status_code == 401:
            # Token might be expired; clear and re-authenticate once
            global _WATTTIME_TOKEN_CACHE
            _WATTTIME_TOKEN_CACHE = None
            token = _get_watttime_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
                resp = requests.get(
                    f"https://api.watttime.org/v3/forecast?region={target_region}&signal_type=co2_moer",
                    headers=headers,
                    timeout=1.5,
                )

        if resp.status_code == 200:
            payload = resp.json()
            data_points = payload.get("data", [])
            if data_points:
                lbs_per_mwh = data_points[0].get("value")
                if lbs_per_mwh is not None:
                    # Conversion: 1 lb/MWh = 0.45359237 g/kWh
                    g_co2_per_kwh = float(lbs_per_mwh) * 0.45359237
                    return round(g_co2_per_kwh, 2)
    except Exception:
        pass
    return None


def get_carbon_intensity(region: str) -> float | None:
    """
    Fetches real-time carbon intensity (gCO2eq / kWh).
    1. Queries UK National Grid API for UK regions.
    2. Queries WattTime API v3 (live MOER forecast) for US/global regions.
    3. Falls back to curated regional averages if network calls fail.
    """
    if not region:
        return None

    # Try UK API
    value = _get_uk_intensity(region)
    if value is not None:
        return value

    # Try WattTime API
    value = _get_watttime_intensity(region)
    if value is not None:
        return value

    # Fallback to standard regional average if offline or unmapped
    return REGIONAL_FALLBACK_CI.get(region, REGIONAL_FALLBACK_CI.get(region.upper(), 380.0))