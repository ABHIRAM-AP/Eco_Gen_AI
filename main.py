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

from pathlib import Path
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

# Load environment variables (.env)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

from src.ingestion_layer.main import app as ingestion_app
from src.analytical_engine.main import app as analytics_app

# Root application
root_app = FastAPI(
    title="EcoGen-AI Platform",
    description=(
        "Unified entry point for the EcoGen-AI carbon footprint platform.\n\n"
        "| Path | Layer | Role |\n"
        "|---|---|---|\n"
        "| `/dashboard` | UI | Interactive Executive Dashboard |\n"
        "| `/ingest` | Layer 1 | Ingestion & Monitoring |\n"
        "| `/analytics` | Layer 2 | Analytical Engine (kWh, gCO2eq) |\n"
    ),
    version="2.0.0",
)

# Enable CORS for local development and multi-origin requests
root_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def root_health():
    """Platform-wide health check. Lists all mounted sub-applications."""
    return {
        "platform": "EcoGen-AI",
        "status": "operational",
        "dashboard": "/dashboard",
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


@root_app.get("/dashboard", response_class=FileResponse, tags=["Dashboard"])
def get_dashboard():
    """Serves the interactive EcoGen-AI executive frontend dashboard."""
    return FileResponse(STATIC_DIR / "index.html")


@root_app.get("/", tags=["Dashboard & Health"])
def root_endpoint(request: Request):
    """
    Platform entry point:
    - In web browsers (Accept: text/html): renders the interactive dashboard.
    - In API clients / test suites (Accept: application/json or */*): returns health JSON.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return FileResponse(STATIC_DIR / "index.html")
    return root_health()


# Mount static assets & sub-applications
root_app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
root_app.mount("/ingest", ingestion_app)
root_app.mount("/analytics", analytics_app)


if __name__ == "__main__":
    uvicorn.run("main:root_app", host="0.0.0.0", port=8000, reload=True)