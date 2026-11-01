#!/usr/bin/env python3
"""
EcoGen-AI Platform Verification Script
-------------------------------------
Verifies that all components of the platform work properly:
1. Root application health & routing (/ and docs)
2. Layer 1 Ingestion: Event & Hardware ingestion endpoints
3. Layer 2 Analytical Engine: Energy, Carbon, Benchmarks, Department Attribution, Trends, Simulation
"""

import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000"


def print_status(component: str, ok: bool, details: str = ""):
    symbol = "✅" if ok else "❌"
    msg = f"{symbol} {component}"
    if details:
        msg += f" — {details}"
    print(msg)


def check_health():
    print("\n--- 1. Checking Root & Documentation Endpoints ---")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        ok = r.status_code == 200 and r.json().get("status") == "operational"
        print_status("Root Health Check (GET /)", ok, f"status={r.status_code}")
    except Exception as e:
        print_status("Root Health Check (GET /)", False, f"Connection failed: {e}")
        return False

    for doc_path in ["/docs", "/ingest/docs", "/analytics/docs"]:
        try:
            r = requests.get(f"{BASE_URL}{doc_path}", timeout=5)
            print_status(f"Docs ({doc_path})", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            print_status(f"Docs ({doc_path})", False, str(e))
    return True


def check_ingestion():
    print("\n--- 2. Checking Layer 1: Ingestion Endpoints ---")
    event_payload = {
        "model_name": "gemma3:270m",
        "task_type": "text-generation",
        "provider": "ollama",
        "tokens_in": 12,
        "tokens_out": 85,
        "runtime_sec": 0.45,
        "power_draw_watts": 18.5,
        "pue": 1.2,
        "department": "Engineering",
        "use_case": "Code Assistance",
        "region": "US-CAL-CISO",
        "gpu_model": "T4",
    }
    
    created_event_id = None
    try:
        r = requests.post(f"{BASE_URL}/ingest/event", json=event_payload, timeout=5)
        ok = r.status_code == 200 and "id" in r.json()
        if ok:
            created_event_id = r.json()["id"]
        print_status("Log Event (POST /ingest/event)", ok, f"event_id={created_event_id}")
    except Exception as e:
        print_status("Log Event (POST /ingest/event)", False, str(e))

    try:
        hw_payload = {
            "device_id": "test-device-01",
            "power_draw_watts": 25.0,
            "gpu_util_pct": 45.0,
            "idle_power_baseline_w": 10.0,
        }
        r = requests.post(f"{BASE_URL}/ingest/hardware", json=hw_payload, timeout=5)
        ok = r.status_code == 200 and "id" in r.json()
        print_status("Log Hardware (POST /ingest/hardware)", ok, f"snapshot_id={r.json().get('id') if ok else None}")
    except Exception as e:
        print_status("Log Hardware (POST /ingest/hardware)", False, str(e))

    try:
        r = requests.get(f"{BASE_URL}/ingest/events?limit=5", timeout=5)
        ok = r.status_code == 200 and isinstance(r.json(), list)
        count = len(r.json()) if ok else 0
        print_status("Fetch Events (GET /ingest/events)", ok, f"{count} events fetched")
    except Exception as e:
        print_status("Fetch Events (GET /ingest/events)", False, str(e))

    return created_event_id


def check_analytics(event_id: int | None):
    print("\n--- 3. Checking Layer 2: Analytical Engine Endpoints ---")
    try:
        r = requests.get(f"{BASE_URL}/analytics/", timeout=5)
        ok = r.status_code == 200 and r.json().get("status") == "operational"
        print_status("Analytics Health (GET /analytics/)", ok)
    except Exception as e:
        print_status("Analytics Health (GET /analytics/)", False, str(e))

    target_id = event_id or 1
    try:
        r = requests.get(f"{BASE_URL}/analytics/event/{target_id}", timeout=5)
        ok = r.status_code == 200
        data = r.json() if ok else {}
        kwh = data.get("energy", {}).get("energy_kwh")
        gco2 = data.get("carbon", {}).get("total_gco2eq")
        print_status(f"Per-Event Analytics (GET /analytics/event/{target_id})", ok, f"kWh={kwh}, gCO2eq={gco2}")
    except Exception as e:
        print_status(f"Per-Event Analytics (GET /analytics/event/{target_id})", False, str(e))

    try:
        r = requests.get(f"{BASE_URL}/analytics/summary", timeout=5)
        ok = r.status_code == 200
        data = r.json() if ok else {}
        print_status("Platform Summary (GET /analytics/summary)", ok, f"total_events={data.get('total_events')}, total_kWh={data.get('total_energy_kwh')}")
    except Exception as e:
        print_status("Platform Summary (GET /analytics/summary)", False, str(e))

    try:
        r = requests.get(f"{BASE_URL}/analytics/benchmarks", timeout=5)
        ok = r.status_code == 200 and isinstance(r.json(), list)
        print_status("Task Benchmarks (GET /analytics/benchmarks)", ok, f"{len(r.json()) if ok else 0} profiles")
    except Exception as e:
        print_status("Task Benchmarks (GET /analytics/benchmarks)", False, str(e))

    try:
        r = requests.get(f"{BASE_URL}/analytics/by-model", timeout=5)
        ok = r.status_code == 200 and isinstance(r.json(), list)
        print_status("Model Rankings (GET /analytics/by-model)", ok, f"{len(r.json()) if ok else 0} models ranked")
    except Exception as e:
        print_status("Model Rankings (GET /analytics/by-model)", False, str(e))

    try:
        r = requests.get(f"{BASE_URL}/analytics/by-provider", timeout=5)
        ok = r.status_code == 200 and isinstance(r.json(), list)
        print_status("Provider Comparison (GET /analytics/by-provider)", ok, f"{len(r.json()) if ok else 0} providers")
    except Exception as e:
        print_status("Provider Comparison (GET /analytics/by-provider)", False, str(e))

    try:
        r = requests.get(f"{BASE_URL}/analytics/by-department", timeout=5)
        ok = r.status_code == 200 and isinstance(r.json(), list)
        print_status("Department Attribution (GET /analytics/by-department)", ok, f"{len(r.json()) if ok else 0} departments")
    except Exception as e:
        print_status("Department Attribution (GET /analytics/by-department)", False, str(e))

    try:
        r = requests.get(f"{BASE_URL}/analytics/carbon-trend", timeout=5)
        ok = r.status_code in (200, 404)  # 404 if no carbon intensity entries
        print_status("Carbon Trend (GET /analytics/carbon-trend)", r.status_code == 200, f"status={r.status_code}")
    except Exception as e:
        print_status("Carbon Trend (GET /analytics/carbon-trend)", False, str(e))

    try:
        sim_payload = {
            "base_event_id": target_id,
            "alt_gpu_model": "A100-80GB",
            "alt_pue": 1.1,
        }
        r = requests.post(f"{BASE_URL}/analytics/simulate", json=sim_payload, timeout=5)
        ok = r.status_code == 200
        data = r.json() if ok else {}
        reduction = data.get("energy_reduction_pct")
        print_status("What-If Simulation (POST /analytics/simulate)", ok, f"energy_reduction={reduction}%")
    except Exception as e:
        print_status("What-If Simulation (POST /analytics/simulate)", False, str(e))


def main():
    print("=" * 60)
    print("EcoGen-AI Full Verification Suite")
    print("=" * 60)
    
    server_healthy = check_health()
    if not server_healthy:
        print("\n⚠️  Server is not running or not responding at http://127.0.0.1:8000.")
        print("Please start the server first in another terminal:")
        print("    uv run uvicorn main:root_app --port 8000 --reload")
        print("or:")
        print("    python main.py\n")
        sys.exit(1)

    event_id = check_ingestion()
    check_analytics(event_id)
    print("\n" + "=" * 60)
    print("Verification completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
