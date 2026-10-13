"""
EcoGen-AI — Root Application
=============================
Mounts both layers as FastAPI sub-applications on a single ASGI server:

  /          → Root health check (this file)
  /ingest/*  → Layer 1: Ingestion & Monitoring
  /analytics/* → Layer 2: Analytical Engine

Run with:
    uv run uvicorn main:root_app --reload --port 8000
or:
    python main.py
"""

import uvicorn
from fastapi import FastAPI

from src.ingestion_layer.main import app as ingestion_app
from src.analytical_engine.main import app as analytics_app

# ---------------------------------------------------------------------------
# Root application
# ---------------------------------------------------------------------------
root_app = FastAPI(
    title="EcoGen-AI Platform",
    description=(
        "Unified entry point for the EcoGen-AI carbon footprint platform.\n\n"
        "| Path | Layer | Role |\n"
        "|---|---|---|\n"
        "| `/ingest` | Layer 1 | Ingestion & Monitoring |\n"
        "| `/analytics` | Layer 2 | Analytical Engine (kWh, gCO2eq) |\n"
    ),
    version="2.0.0",
)


@root_app.get("/", tags=["Health"])
def root_health():
    """Platform-wide health check. Lists all mounted sub-applications."""
    return {
        "platform": "EcoGen-AI",
        "status": "operational",
        "layers": {
            "layer1_ingestion": {
                "mount": "/ingest",
                "docs": "/ingest/docs",
                "description": "Intercepts LLM calls and logs runtime, tokens, power draw.",
            },
            "layer2_analytics": {
                "mount": "/analytics",
                "docs": "/analytics/docs",
                "description": "Computes kWh, gCO2eq, benchmarks, and what-if simulations.",
            },
        },
    }


# ---------------------------------------------------------------------------
# Mount sub-applications
# ---------------------------------------------------------------------------
root_app.mount("/ingest", ingestion_app)
root_app.mount("/analytics", analytics_app)


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:root_app", host="0.0.0.0", port=8000, reload=True)