"""
Carbon Calculator — Layer 2 Analytical Engine
----------------------------------------------
Computes:
  1. Operational carbon (GHG Scope 2):
       Scope2_gCO2eq = energy_kwh × carbon_intensity_gCO2_per_kWh

  2. Embodied carbon amortization (GHG Scope 3):
       Manufacturing emissions of the GPU amortized over its expected lifespan,
       proportional to the fraction of lifespan consumed by this inference event.

       Embodied_gCO2eq = manufacturing_gCO2eq
                         / (lifespan_years × 365.25 × 24 × 3600)
                         × runtime_sec

References:
    - GHG Protocol Scope 2 and Scope 3 guidance
    - Lannelongue et al. (2021) "Green Algorithms: Quantifying the Carbon Footprint of Computation"
    - Strubell et al. (2019) "Energy and Policy Considerations for Deep Learning in NLP"
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from ..models.gpu_tdp_map import get_gpu_embodied_carbon
from ..schemas.schema import EnergyBreakdown, CarbonBreakdown

# Default carbon intensity (gCO2eq/kWh) used as last-resort fallback.
# Represents the approximate global average grid carbon intensity (IEA 2023).
_GLOBAL_AVG_CARBON_INTENSITY: float = 436.0

# Seconds in a year (accounting for leap years)
_SECONDS_PER_YEAR: float = 365.25 * 24 * 3600


def compute_carbon(
    energy: EnergyBreakdown,
    carbon_intensity: Optional[float],
    gpu_model: Optional[str],
    runtime_sec: Optional[float],
    hardware_install_date: Optional[datetime],
) -> CarbonBreakdown:
    """
    Compute the full carbon footprint for an inference event.

    Args:
        energy:               Completed EnergyBreakdown from the energy calculator.
        carbon_intensity:     Grid carbon intensity in gCO2eq/kWh.
                              Stored by Layer 1; falls back to global average if None.
        gpu_model:            GPU model string for embodied carbon lookup.
        runtime_sec:          Inference wall-clock duration in seconds.
        hardware_install_date: When the GPU was deployed (used to decide
                              whether embodied amortization is computable).

    Returns:
        CarbonBreakdown Pydantic model.
    """
    # ── Resolve carbon intensity ─────────────────────────────────────────────
    ci = carbon_intensity if carbon_intensity is not None else _GLOBAL_AVG_CARBON_INTENSITY
    ci_note = (
        "stored_by_layer1" if carbon_intensity is not None
        else f"global_avg_fallback ({_GLOBAL_AVG_CARBON_INTENSITY} gCO2eq/kWh)"
    )

    # ── Scope 2: Operational carbon ──────────────────────────────────────────
    operational_gco2eq = energy.energy_kwh * ci

    # ── Scope 3: Embodied carbon amortization ────────────────────────────────
    embodied_gco2eq: Optional[float] = None
    embodied_note: Optional[str] = None

    if gpu_model and runtime_sec and runtime_sec > 0:
        gpu_data = get_gpu_embodied_carbon(gpu_model)
        manufacturing_gco2eq = gpu_data["manufacturing_gco2eq"]
        lifespan_years = gpu_data["lifespan_years"]

        # Rate: gCO2eq emitted per second of GPU lifespan
        gco2eq_per_second = manufacturing_gco2eq / (lifespan_years * _SECONDS_PER_YEAR)
        embodied_gco2eq = gco2eq_per_second * runtime_sec
        embodied_note = (
            f"amortized from {manufacturing_gco2eq:,.0f} gCO2eq "
            f"over {lifespan_years}yr lifespan ({gpu_model})"
        )
    elif not gpu_model:
        embodied_note = "skipped — gpu_model not provided"
    else:
        embodied_note = "skipped — runtime_sec is zero or None"

    # ── Total carbon ─────────────────────────────────────────────────────────
    total_gco2eq = operational_gco2eq + (embodied_gco2eq or 0.0)

    return CarbonBreakdown(
        event_id=energy.event_id,
        carbon_intensity_gco2_per_kwh=round(ci, 4),
        operational_gco2eq=round(operational_gco2eq, 6),
        gpu_model=gpu_model,
        embodied_gco2eq=round(embodied_gco2eq, 6) if embodied_gco2eq is not None else None,
        embodied_note=embodied_note,
        total_gco2eq=round(total_gco2eq, 6),
    )


def compute_embodied_carbon(
    gpu_model: Optional[str],
    runtime_sec: float,
) -> Optional[float]:
    """
    Standalone helper: compute only the embodied (Scope 3) amortized carbon
    for a given GPU model and runtime duration.

    Returns gCO2eq, or None if gpu_model is missing.
    """
    if not gpu_model or runtime_sec <= 0:
        return None

    gpu_data = get_gpu_embodied_carbon(gpu_model)
    manufacturing_gco2eq = gpu_data["manufacturing_gco2eq"]
    lifespan_years = gpu_data["lifespan_years"]

    gco2eq_per_second = manufacturing_gco2eq / (lifespan_years * _SECONDS_PER_YEAR)
    return round(gco2eq_per_second * runtime_sec, 6)
