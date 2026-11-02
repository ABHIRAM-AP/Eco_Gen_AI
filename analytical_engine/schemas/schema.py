"""
Pydantic Output Schemas — Layer 2 Analytical Engine
----------------------------------------------------
All response models returned by the /analytics/* endpoints.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Energy Breakdown
# ---------------------------------------------------------------------------

class EnergyBreakdown(BaseModel):
    """
    Detailed energy consumption breakdown for a single inference event.
    Energy is always expressed in kilowatt-hours (kWh).
    """
    event_id: int
    computation_tier: str = Field(
        description="'tier1_measured' if real power data was used, 'tier2_flops' if estimated."
    )
    # Power components (Watts)
    active_power_w: Optional[float] = Field(None, description="Measured/estimated active power draw in Watts.")
    idle_power_w: float = Field(0.0, description="Baseline idle power in Watts (0 if no snapshot available).")
    incremental_power_w: float = Field(description="Active minus idle power (net workload power).")
    pue_factor: float = Field(description="Power Usage Effectiveness multiplier applied.")
    num_gpus: int = Field(1, description="Number of GPUs scaled over.")

    # Energy outputs (kWh)
    raw_energy_kwh: float = Field(description="Energy from net workload power, before PUE.")
    energy_kwh: float = Field(description="Final energy including PUE and GPU count scaling.")

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Carbon Breakdown
# ---------------------------------------------------------------------------

class CarbonBreakdown(BaseModel):
    """
    Carbon footprint breakdown for a single inference event.
    All values in grams of CO2-equivalent (gCO2eq).
    """
    event_id: int

    # Operational carbon (GHG Scope 2)
    carbon_intensity_gco2_per_kwh: float = Field(
        description="Grid carbon intensity used (gCO2eq/kWh). Stored by Layer 1 or fetched live."
    )
    operational_gco2eq: float = Field(
        description="Scope 2 emissions: energy_kwh × carbon_intensity."
    )

    # Embodied carbon (GHG Scope 3)
    gpu_model: Optional[str] = None
    embodied_gco2eq: Optional[float] = Field(
        None,
        description="Amortized manufacturing carbon for this event's runtime duration."
    )
    embodied_note: Optional[str] = Field(
        None,
        description="Explains source or why embodied carbon is None."
    )

    # Totals
    total_gco2eq: float = Field(
        description="Operational + embodied carbon (embodied treated as 0 if unavailable)."
    )

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Per-event full analytics
# ---------------------------------------------------------------------------

class EventAnalytics(BaseModel):
    """
    Complete analytics result for a single InferenceEvent.
    Combines energy, carbon, and efficiency metrics.
    """
    event_id: int
    model_name: str
    task_type: Optional[str]
    provider: Optional[str]
    department: Optional[str]
    use_case: Optional[str]
    timestamp: datetime

    # Sub-breakdowns
    energy: EnergyBreakdown
    carbon: CarbonBreakdown

    # Efficiency metrics
    tokens_total: Optional[int] = Field(None, description="tokens_in + tokens_out.")
    tokens_per_kwh: Optional[float] = Field(None, description="Throughput efficiency.")
    gco2eq_per_1k_tokens: Optional[float] = Field(None, description="Carbon per 1,000 tokens.")
    energy_per_token_uj: Optional[float] = Field(
        None,
        description="Energy per token in micro-joules (μJ). 1 kWh = 3.6×10^9 μJ."
    )
    cost_usd: Optional[float] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Benchmark Report (per task type)
# ---------------------------------------------------------------------------

class BenchmarkReport(BaseModel):
    """
    Aggregated energy and carbon statistics for a specific task type.
    Suitable for cross-task-type comparison (text vs image vs fine-tuning).
    """
    task_type: str
    event_count: int

    # Energy stats (kWh)
    avg_energy_kwh: float
    min_energy_kwh: float
    max_energy_kwh: float
    p50_energy_kwh: float
    p95_energy_kwh: float
    total_energy_kwh: float

    # Carbon stats (gCO2eq)
    avg_carbon_gco2eq: float
    total_carbon_gco2eq: float

    # Efficiency stats
    avg_tokens_per_kwh: Optional[float]
    avg_gco2eq_per_1k_tokens: Optional[float]


# ---------------------------------------------------------------------------
# Model Rankings
# ---------------------------------------------------------------------------

class ModelRanking(BaseModel):
    """
    Energy and carbon efficiency ranking for a model.
    Useful for identifying the most/least efficient models.
    """
    model_name: str
    event_count: int
    total_energy_kwh: float
    avg_energy_kwh: float
    total_carbon_gco2eq: float
    avg_carbon_gco2eq: float
    avg_tokens_per_kwh: Optional[float]
    avg_gco2eq_per_1k_tokens: Optional[float]
    provider: Optional[str]


# ---------------------------------------------------------------------------
# Provider Comparison
# ---------------------------------------------------------------------------

class ProviderComparison(BaseModel):
    """
    Cross-provider carbon and energy comparison.
    e.g., 'gemini' vs 'ollama' efficiency.
    """
    provider: str
    event_count: int
    total_energy_kwh: float
    avg_energy_kwh: float
    total_carbon_gco2eq: float
    avg_carbon_gco2eq: float
    avg_tokens_per_kwh: Optional[float]


# ---------------------------------------------------------------------------
# Department Attribution (ESG Reporting)
# ---------------------------------------------------------------------------

class DepartmentAttribution(BaseModel):
    """
    Carbon and energy attribution broken down by department/cost center.
    Supports internal ESG reporting and sustainability accounting.
    """
    department: str
    event_count: int
    total_energy_kwh: float
    total_carbon_gco2eq: float
    total_cost_usd: Optional[float]
    avg_carbon_per_event_gco2eq: float
    carbon_share_pct: Optional[float] = Field(
        None,
        description="This department's share of total platform carbon footprint (%)."
    )


# ---------------------------------------------------------------------------
# Carbon Intensity Trend
# ---------------------------------------------------------------------------

class CarbonTrendPoint(BaseModel):
    """
    A single data point in the carbon intensity time series.
    """
    timestamp: datetime
    region: Optional[str]
    carbon_intensity_gco2_per_kwh: float
    event_id: int
    model_name: str


# ---------------------------------------------------------------------------
# Summary Report (platform-wide)
# ---------------------------------------------------------------------------

class SummaryReport(BaseModel):
    """
    Platform-wide aggregate snapshot of energy and carbon consumption.
    """
    total_events: int
    date_range_start: Optional[datetime]
    date_range_end: Optional[datetime]

    # Totals
    total_energy_kwh: float
    total_carbon_gco2eq: float
    total_tokens_processed: Optional[int]
    total_cost_usd: Optional[float]

    # Averages
    avg_energy_kwh_per_event: float
    avg_carbon_gco2eq_per_event: float
    avg_carbon_intensity_gco2_per_kwh: Optional[float]

    # Breakdowns (top-level counts)
    unique_models: int
    unique_providers: int
    unique_departments: int
    task_type_counts: dict[str, int]

    # Tier coverage
    tier1_event_count: int
    tier2_event_count: int


# ---------------------------------------------------------------------------
# Simulation (what-if analysis)
# ---------------------------------------------------------------------------

class SimulationRequest(BaseModel):
    """
    Input for what-if simulation endpoint.
    Models an alternative scenario for an existing event.
    """
    base_event_id: int = Field(description="The InferenceEvent ID to base the simulation on.")
    alt_model_name: Optional[str] = Field(None, description="Swap the model (affects param_count lookup).")
    alt_gpu_model: Optional[str] = Field(None, description="Swap the GPU hardware.")
    alt_num_gpus: Optional[int] = Field(None, description="Change the number of GPUs.")
    alt_batch_size: Optional[int] = Field(None, description="Simulate a different batch size.")
    alt_region: Optional[str] = Field(None, description="Change the grid region (affects carbon intensity).")
    alt_pue: Optional[float] = Field(None, description="Apply a different PUE (e.g., 1.0 for 100% renewable DC).")
    alt_carbon_intensity: Optional[float] = Field(None, description="Override carbon intensity directly (gCO2eq/kWh).")


class SimulationResult(BaseModel):
    """
    Output of a what-if simulation, showing original vs. simulated metrics.
    """
    base_event_id: int

    # Original metrics
    original_energy_kwh: float
    original_carbon_gco2eq: float

    # Simulated metrics
    simulated_energy_kwh: float
    simulated_carbon_gco2eq: float

    # Deltas
    energy_delta_kwh: float
    carbon_delta_gco2eq: float
    energy_reduction_pct: float
    carbon_reduction_pct: float

    # Scenario description
    changes_applied: List[str] = Field(description="Human-readable list of what was changed in the simulation.")
