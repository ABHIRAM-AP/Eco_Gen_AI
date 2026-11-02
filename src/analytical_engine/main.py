"""
EcoGen-AI — Layer 2: Analytical Engine API
-------------------------------------------
FastAPI application exposing all /analytics/* endpoints.

Data flow:
  1. Fetch raw InferenceEvent rows from ecogen.db (written by Layer 1).
  2. Look up the closest HardwareSnapshot to get idle_power_baseline_w.
  3. Run compute_energy() → EnergyBreakdown.
  4. Run compute_carbon() → CarbonBreakdown.
  5. Assemble EventAnalytics and return/aggregate.

Mount alongside Layer 1 by adding:
    from src.analytical_engine.main import app as analytics_app
    root_app.mount("/analytics", analytics_app)
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from ..ingestion_layer.collectors.carbon_api import get_carbon_intensity
from ..ingestion_layer.models.model import HardwareSnapshot, InferenceEvent
from .calculators.benchmarks import (
    compute_benchmark_report,
    compute_carbon_trend,
    compute_department_attribution,
    compute_model_rankings,
    compute_provider_comparison,
)
from .calculators.carbon import compute_carbon
from .calculators.energy import compute_energy
from .database.db import get_database
from .schemas.schema import (
    BenchmarkReport,
    CarbonTrendPoint,
    DepartmentAttribution,
    EventAnalytics,
    ModelRanking,
    ProviderComparison,
    SimulationRequest,
    SimulationResult,
    SummaryReport,
)

app = FastAPI(
    title="EcoGen-AI Analytical Engine",
    description=(
        "Layer 2: Converts raw ingestion data into actionable energy (kWh) "
        "and carbon (gCO2eq) metrics, and benchmarks resource usage across "
        "task types (text generation, image generation, fine-tuning)."
    ),
    version="2.0.0",
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_idle_power(event: InferenceEvent, db: Session) -> float:
    """
    Look up the most recent HardwareSnapshot recorded at or before the event
    timestamp to obtain the idle_power_baseline_w.

    Falls back to 0.0 if no hardware snapshot exists.
    """
    snapshot: Optional[HardwareSnapshot] = (
        db.query(HardwareSnapshot)
        .filter(
            HardwareSnapshot.timestamp <= event.timestamp,
            HardwareSnapshot.idle_power_baseline_w.isnot(None),
        )
        .order_by(HardwareSnapshot.timestamp.desc())
        .first()
    )
    if snapshot and snapshot.idle_power_baseline_w is not None:
        return float(snapshot.idle_power_baseline_w)
    return 0.0


def _get_hardware_install_date(event: InferenceEvent, db: Session) -> Optional[datetime]:
    """
    Fetch hardware_install_date from the most recent HardwareSnapshot
    (for embodied carbon amortization).
    """
    snapshot: Optional[HardwareSnapshot] = (
        db.query(HardwareSnapshot)
        .filter(HardwareSnapshot.hardware_install_date.isnot(None))
        .order_by(HardwareSnapshot.timestamp.desc())
        .first()
    )
    return snapshot.hardware_install_date if snapshot else None


def _build_event_analytics(event: InferenceEvent, db: Session) -> EventAnalytics:
    """
    Full analytics pipeline for a single InferenceEvent.
    """
    idle_power_w = _get_idle_power(event, db)
    hw_install_date = _get_hardware_install_date(event, db)

    energy = compute_energy(
        event_id=event.id,
        power_draw_watts=event.power_draw_watts,
        runtime_sec=event.runtime_sec,
        pue=event.pue,
        num_gpus_used=event.num_gpus_used,
        idle_power_w=idle_power_w,
        active_param_count_b=event.active_param_count_b,
        tokens_in=event.tokens_in,
        tokens_out=event.tokens_out,
        gpu_model=event.gpu_model,
    )

    carbon = compute_carbon(
        energy=energy,
        carbon_intensity=event.carbon_intensity,
        gpu_model=event.gpu_model,
        runtime_sec=event.runtime_sec,
        hardware_install_date=hw_install_date,
    )

    # Efficiency metrics
    tokens_total = (event.tokens_in or 0) + (event.tokens_out or 0)
    tokens_per_kwh: Optional[float] = None
    gco2eq_per_1k_tokens: Optional[float] = None
    energy_per_token_uj: Optional[float] = None

    if tokens_total > 0 and energy.energy_kwh > 0:
        tokens_per_kwh = round(tokens_total / energy.energy_kwh, 2)
        gco2eq_per_1k_tokens = round((carbon.total_gco2eq / tokens_total) * 1000, 6)
        # 1 kWh = 3.6×10^9 μJ
        energy_per_token_uj = round((energy.energy_kwh * 3.6e9) / tokens_total, 4)

    return EventAnalytics(
        event_id=event.id,
        model_name=event.model_name,
        task_type=event.task_type,
        provider=event.provider,
        department=event.department,
        use_case=event.use_case,
        timestamp=event.timestamp,
        energy=energy,
        carbon=carbon,
        tokens_total=tokens_total if tokens_total > 0 else None,
        tokens_per_kwh=tokens_per_kwh,
        gco2eq_per_1k_tokens=gco2eq_per_1k_tokens,
        energy_per_token_uj=energy_per_token_uj,
        cost_usd=event.cost_usd,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    """Layer 2 health check and capability summary."""
    return {
        "service": "EcoGen-AI Analytical Engine",
        "layer": 2,
        "status": "operational",
        "capabilities": [
            "energy_kwh_computation (tier1_measured + tier2_flops_fallback)",
            "carbon_gco2eq_scope2_and_scope3",
            "task_type_benchmarking",
            "model_efficiency_rankings",
            "provider_comparison",
            "department_esg_attribution",
            "carbon_intensity_trend",
            "what_if_simulation",
        ],
    }


@app.get("/event/{event_id}", response_model=EventAnalytics, tags=["Per-Event Analytics"])
def get_event_analytics(event_id: int, db: Session = Depends(get_database)):
    """
    Full energy and carbon breakdown for a single InferenceEvent.

    Returns:
    - **energy**: kWh breakdown with computation tier (measured vs FLOPs-estimated)
    - **carbon**: Scope 2 (operational) + Scope 3 (embodied) gCO2eq
    - **efficiency**: tokens/kWh, gCO2eq/1K tokens, energy/token in μJ
    """
    event = db.query(InferenceEvent).filter(InferenceEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"InferenceEvent {event_id} not found.")
    return _build_event_analytics(event, db)


@app.get("/summary", response_model=SummaryReport, tags=["Platform Summary"])
def get_summary(
    start: Optional[datetime] = Query(None, description="Filter events from this timestamp (ISO 8601)."),
    end: Optional[datetime] = Query(None, description="Filter events up to this timestamp (ISO 8601)."),
    db: Session = Depends(get_database),
):
    """
    Platform-wide aggregate snapshot of energy and carbon consumption.

    Optionally filter by date range using `start` and `end` query parameters.
    """
    query = db.query(InferenceEvent)
    if start:
        query = query.filter(InferenceEvent.timestamp >= start)
    if end:
        query = query.filter(InferenceEvent.timestamp <= end)

    events = query.order_by(InferenceEvent.timestamp.asc()).all()

    if not events:
        raise HTTPException(status_code=404, detail="No events found for the given filters.")

    analytics = [_build_event_analytics(ev, db) for ev in events]

    total_energy = sum(a.energy.energy_kwh for a in analytics)
    total_carbon = sum(a.carbon.total_gco2eq for a in analytics)
    total_tokens = sum((a.tokens_total or 0) for a in analytics)
    cost_vals = [a.cost_usd for a in analytics if a.cost_usd is not None]
    ci_vals = [a.carbon.carbon_intensity_gco2_per_kwh for a in analytics]

    task_type_counts: dict[str, int] = {}
    for a in analytics:
        k = a.task_type or "unknown"
        task_type_counts[k] = task_type_counts.get(k, 0) + 1

    tier1_count = sum(1 for a in analytics if a.energy.computation_tier == "tier1_measured")
    tier2_count = sum(1 for a in analytics if a.energy.computation_tier == "tier2_flops")

    return SummaryReport(
        total_events=len(analytics),
        date_range_start=events[0].timestamp,
        date_range_end=events[-1].timestamp,
        total_energy_kwh=round(total_energy, 8),
        total_carbon_gco2eq=round(total_carbon, 6),
        total_tokens_processed=total_tokens if total_tokens > 0 else None,
        total_cost_usd=round(sum(cost_vals), 4) if cost_vals else None,
        avg_energy_kwh_per_event=round(total_energy / len(analytics), 8),
        avg_carbon_gco2eq_per_event=round(total_carbon / len(analytics), 6),
        avg_carbon_intensity_gco2_per_kwh=round(sum(ci_vals) / len(ci_vals), 4) if ci_vals else None,
        unique_models=len({ev.model_name for ev in events}),
        unique_providers=len({ev.provider for ev in events if ev.provider}),
        unique_departments=len({ev.department for ev in events if ev.department}),
        task_type_counts=task_type_counts,
        tier1_event_count=tier1_count,
        tier2_event_count=tier2_count,
    )


@app.get("/benchmarks", response_model=List[BenchmarkReport], tags=["Benchmarks"])
def get_benchmarks(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    db: Session = Depends(get_database),
):
    """
    Per-task-type energy and carbon benchmarks.

    Aggregates all events by `task_type` and returns statistical profiles
    (avg, min, max, p50, p95) for energy and carbon.
    Task types include: `text-generation`, `image-generation`, `fine-tuning`, etc.
    """
    query = db.query(InferenceEvent)
    if start:
        query = query.filter(InferenceEvent.timestamp >= start)
    if end:
        query = query.filter(InferenceEvent.timestamp <= end)
    events = query.all()

    if not events:
        raise HTTPException(status_code=404, detail="No events found.")

    analytics = [_build_event_analytics(ev, db) for ev in events]
    return compute_benchmark_report(analytics)


@app.get("/by-model", response_model=List[ModelRanking], tags=["Benchmarks"])
def get_model_rankings(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(20, ge=1, le=100, description="Max number of models to return."),
    db: Session = Depends(get_database),
):
    """
    Model efficiency rankings sorted by average carbon per event (ascending).

    The most carbon-efficient model appears first.
    """
    query = db.query(InferenceEvent)
    if start:
        query = query.filter(InferenceEvent.timestamp >= start)
    if end:
        query = query.filter(InferenceEvent.timestamp <= end)
    events = query.all()

    if not events:
        raise HTTPException(status_code=404, detail="No events found.")

    analytics = [_build_event_analytics(ev, db) for ev in events]
    rankings = compute_model_rankings(analytics)
    return rankings[:limit]


@app.get("/by-provider", response_model=List[ProviderComparison], tags=["Benchmarks"])
def get_provider_comparison(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    db: Session = Depends(get_database),
):
    """
    Cross-provider energy and carbon comparison.
    e.g., gemini cloud inference vs. self-hosted ollama.
    """
    query = db.query(InferenceEvent)
    if start:
        query = query.filter(InferenceEvent.timestamp >= start)
    if end:
        query = query.filter(InferenceEvent.timestamp <= end)
    events = query.all()

    if not events:
        raise HTTPException(status_code=404, detail="No events found.")

    analytics = [_build_event_analytics(ev, db) for ev in events]
    return compute_provider_comparison(analytics)


@app.get("/by-department", response_model=List[DepartmentAttribution], tags=["ESG Attribution"])
def get_department_attribution(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    db: Session = Depends(get_database),
):
    """
    Carbon and energy attribution by department/cost center.

    Sorted by total carbon (highest emitting department first).
    Includes each department's share (%) of total platform carbon footprint.
    """
    query = db.query(InferenceEvent)
    if start:
        query = query.filter(InferenceEvent.timestamp >= start)
    if end:
        query = query.filter(InferenceEvent.timestamp <= end)
    events = query.all()

    if not events:
        raise HTTPException(status_code=404, detail="No events found.")

    analytics = [_build_event_analytics(ev, db) for ev in events]
    return compute_department_attribution(analytics)


@app.get("/carbon-trend", response_model=List[CarbonTrendPoint], tags=["Trends"])
def get_carbon_trend(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_database),
):
    """
    Time-series of carbon intensity values across events.

    Useful for identifying greener grid windows or detecting carbon spikes.
    Results are ordered chronologically (oldest first).
    """
    query = db.query(InferenceEvent).filter(
        InferenceEvent.carbon_intensity.isnot(None)
    )
    if start:
        query = query.filter(InferenceEvent.timestamp >= start)
    if end:
        query = query.filter(InferenceEvent.timestamp <= end)

    events = query.order_by(InferenceEvent.timestamp.asc()).limit(limit).all()

    if not events:
        raise HTTPException(status_code=404, detail="No events with carbon intensity data found.")

    analytics = [_build_event_analytics(ev, db) for ev in events]
    trend_points = compute_carbon_trend(analytics)

    # Enrich with region from the original event
    event_region_map = {ev.id: ev.region for ev in events}
    for point in trend_points:
        point.region = event_region_map.get(point.event_id)

    return trend_points


@app.post("/simulate", response_model=SimulationResult, tags=["What-If Simulation"])
def simulate(request: SimulationRequest, db: Session = Depends(get_database)):
    """
    What-if simulation: compare original event metrics against an alternative scenario.

    Swap any combination of: model, GPU, num_gpus, batch_size, region, PUE, carbon_intensity.
    Returns original vs. simulated energy/carbon and percentage reductions.
    """
    event = db.query(InferenceEvent).filter(InferenceEvent.id == request.base_event_id).first()
    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"InferenceEvent {request.base_event_id} not found."
        )

    idle_power_w = _get_idle_power(event, db)
    hw_install_date = _get_hardware_install_date(event, db)

    # ── Original analytics ────────────────────────────────────────────────
    orig_energy = compute_energy(
        event_id=event.id,
        power_draw_watts=event.power_draw_watts,
        runtime_sec=event.runtime_sec,
        pue=event.pue,
        num_gpus_used=event.num_gpus_used,
        idle_power_w=idle_power_w,
        active_param_count_b=event.active_param_count_b,
        tokens_in=event.tokens_in,
        tokens_out=event.tokens_out,
        gpu_model=event.gpu_model,
    )
    orig_carbon = compute_carbon(
        energy=orig_energy,
        carbon_intensity=event.carbon_intensity,
        gpu_model=event.gpu_model,
        runtime_sec=event.runtime_sec,
        hardware_install_date=hw_install_date,
    )

    # ── Build simulated overrides ─────────────────────────────────────────
    sim_gpu_model = request.alt_gpu_model or event.gpu_model
    sim_num_gpus = request.alt_num_gpus or event.num_gpus_used
    sim_pue = request.alt_pue or event.pue
    sim_carbon_intensity = request.alt_carbon_intensity or event.carbon_intensity

    # If region changes, attempt a live carbon intensity lookup
    if request.alt_region and sim_carbon_intensity is None:
        sim_carbon_intensity = get_carbon_intensity(request.alt_region) or event.carbon_intensity

    # Simulate power: if GPU changed, use None power_draw to trigger Tier 2
    sim_power_draw = None if request.alt_gpu_model else event.power_draw_watts

    # Batch-size efficiency: if batch increases, amortize runtime proportionally
    sim_runtime = event.runtime_sec
    if request.alt_batch_size and event.batch_size and request.alt_batch_size != event.batch_size:
        efficiency_ratio = event.batch_size / request.alt_batch_size
        sim_runtime = (event.runtime_sec or 0.0) * efficiency_ratio

    sim_energy = compute_energy(
        event_id=event.id,
        power_draw_watts=sim_power_draw,
        runtime_sec=sim_runtime,
        pue=sim_pue,
        num_gpus_used=sim_num_gpus,
        idle_power_w=idle_power_w,
        active_param_count_b=event.active_param_count_b,
        tokens_in=event.tokens_in,
        tokens_out=event.tokens_out,
        gpu_model=sim_gpu_model,
    )
    sim_carbon = compute_carbon(
        energy=sim_energy,
        carbon_intensity=sim_carbon_intensity,
        gpu_model=sim_gpu_model,
        runtime_sec=sim_runtime,
        hardware_install_date=hw_install_date,
    )

    # ── Compute deltas ────────────────────────────────────────────────────
    orig_e = orig_energy.energy_kwh
    sim_e = sim_energy.energy_kwh
    orig_c = orig_carbon.total_gco2eq
    sim_c = sim_carbon.total_gco2eq

    energy_delta = sim_e - orig_e
    carbon_delta = sim_c - orig_c

    energy_reduction_pct = round(((orig_e - sim_e) / orig_e * 100) if orig_e > 0 else 0.0, 2)
    carbon_reduction_pct = round(((orig_c - sim_c) / orig_c * 100) if orig_c > 0 else 0.0, 2)

    # ── Document what changed ─────────────────────────────────────────────
    changes: list[str] = []
    if request.alt_model_name:
        changes.append(f"model: {event.model_name} → {request.alt_model_name}")
    if request.alt_gpu_model:
        changes.append(f"gpu: {event.gpu_model or 'none'} → {request.alt_gpu_model}")
    if request.alt_num_gpus:
        changes.append(f"num_gpus: {event.num_gpus_used} → {request.alt_num_gpus}")
    if request.alt_batch_size:
        changes.append(f"batch_size: {event.batch_size} → {request.alt_batch_size}")
    if request.alt_region:
        changes.append(f"region: {event.region or 'none'} → {request.alt_region}")
    if request.alt_pue:
        changes.append(f"pue: {event.pue} → {request.alt_pue}")
    if request.alt_carbon_intensity:
        changes.append(f"carbon_intensity: {event.carbon_intensity} → {request.alt_carbon_intensity}")
    if not changes:
        changes.append("no changes applied (simulation mirrors original)")

    return SimulationResult(
        base_event_id=event.id,
        original_energy_kwh=round(orig_e, 8),
        original_carbon_gco2eq=round(orig_c, 6),
        simulated_energy_kwh=round(sim_e, 8),
        simulated_carbon_gco2eq=round(sim_c, 6),
        energy_delta_kwh=round(energy_delta, 8),
        carbon_delta_gco2eq=round(carbon_delta, 6),
        energy_reduction_pct=energy_reduction_pct,
        carbon_reduction_pct=carbon_reduction_pct,
        changes_applied=changes,
    )
