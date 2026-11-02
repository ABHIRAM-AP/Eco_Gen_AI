"""
Energy Calculator — Layer 2 Analytical Engine
----------------------------------------------
Computes inference energy consumption in kilowatt-hours (kWh).

Tier 1 (Measured):
    Uses actual power_draw_watts from the InferenceEvent.
    E = (P_active - P_idle) × runtime_sec × PUE × num_gpus / 3_600_000

Tier 2 (FLOPs-based estimation — fallback when power is unmeasured):
    Estimates GPU utilization from the number of FLOPs executed,
    relative to the GPU's peak theoretical throughput.
    FLOPs ≈ 2 × active_param_count_b × 1e9 × total_tokens
    E ≈ (FLOPs / peak_TFLOPS / 1e12) × TDP_W × PUE × num_gpus / 3_600_000

References:
    - Patterson et al. (2021) "Carbon and the Broad Economy of Machine Learning"
    - Lottick et al. (2019) "Energy Usage Reports for Neural Network Training"
    - Lacoste et al. (2019) "Quantifying the Carbon Intensity of AI in Cloud Instances"
"""

from __future__ import annotations
from typing import Optional

from ..models.gpu_tdp_map import get_gpu_tdp, get_gpu_peak_tflops
from ..schemas.schema import EnergyBreakdown

# Conversion constant: 1 kWh = 3,600,000 watt-seconds (Ws)
_WS_PER_KWH: float = 3_600_000.0

# Hardware utilization efficiency factor for Tier 2
# Real-world GPU utilization during inference is typically 30-70% of peak TFLOPS.
# We use a conservative 0.45 (45%) as the effective utilization coefficient.
_HW_UTILIZATION_EFFICIENCY: float = 0.45


def _tier1_energy(
    active_power_w: float,
    idle_power_w: float,
    runtime_sec: float,
    pue: float,
    num_gpus: int,
) -> tuple[float, float]:
    """
    Compute energy from measured power readings.

    Returns:
        (raw_energy_kwh, energy_kwh_with_pue_and_gpus)
    """
    incremental_w = max(active_power_w - idle_power_w, 0.0)
    raw_kwh = (incremental_w * runtime_sec) / _WS_PER_KWH
    total_kwh = raw_kwh * pue * num_gpus
    return raw_kwh, total_kwh


def _tier2_energy(
    active_param_count_b: float,
    tokens_in: int,
    tokens_out: int,
    gpu_model: Optional[str],
    idle_power_w: float,
    runtime_sec: float,
    pue: float,
    num_gpus: int,
) -> tuple[float, float, float]:
    """
    Estimate energy from FLOPs when real power draw is unavailable.

    FLOPs per token = 2 × active_parameters (standard dense forward-pass estimate).
    GPU utilization = actual_flops / (peak_tflops × runtime_sec)
    Effective power = utilization × TDP × efficiency_factor

    Returns:
        (estimated_active_power_w, raw_energy_kwh, energy_kwh_with_pue_and_gpus)
    """
    total_tokens = (tokens_in or 0) + (tokens_out or 0)
    params = active_param_count_b * 1e9  # convert billions → count

    # FLOPs for a single forward pass: 2 × params × tokens
    total_flops = 2.0 * params * total_tokens

    # GPU peak throughput in FLOPS/second
    peak_tflops = get_gpu_peak_tflops(gpu_model)
    peak_flops_per_sec = peak_tflops * 1e12

    # Estimated GPU utilization fraction (clamped 0–1)
    if peak_flops_per_sec > 0 and runtime_sec > 0:
        utilization = min(total_flops / (peak_flops_per_sec * runtime_sec), 1.0)
    else:
        utilization = _HW_UTILIZATION_EFFICIENCY  # fallback flat estimate

    # Apply hardware efficiency coefficient
    effective_utilization = utilization * _HW_UTILIZATION_EFFICIENCY

    gpu_tdp_w = get_gpu_tdp(gpu_model)
    estimated_active_w = effective_utilization * gpu_tdp_w

    incremental_w = max(estimated_active_w - idle_power_w, 0.0)
    raw_kwh = (incremental_w * runtime_sec) / _WS_PER_KWH
    total_kwh = raw_kwh * pue * num_gpus

    return estimated_active_w, raw_kwh, total_kwh


def compute_energy(
    event_id: int,
    power_draw_watts: Optional[float],
    runtime_sec: Optional[float],
    pue: Optional[float],
    num_gpus_used: Optional[int],
    idle_power_w: float = 0.0,
    # Tier 2 fields
    active_param_count_b: Optional[float] = None,
    tokens_in: Optional[int] = 0,
    tokens_out: Optional[int] = 0,
    gpu_model: Optional[str] = None,
) -> EnergyBreakdown:
    """
    Primary entry point for energy computation.

    Selects Tier 1 (measured) automatically if `power_draw_watts` is available.
    Falls back to Tier 2 (FLOPs estimate) if power is missing but
    `active_param_count_b` is available.

    If neither is available, returns a zero-energy result with a clear tier label.

    Args:
        event_id:            InferenceEvent primary key (for traceability).
        power_draw_watts:    Measured GPU/CPU power during inference (Watts).
        runtime_sec:         Inference wall-clock duration (seconds).
        pue:                 Datacenter Power Usage Effectiveness factor.
        num_gpus_used:       Number of GPUs in use.
        idle_power_w:        Resting power baseline from HardwareSnapshot (Watts).
        active_param_count_b: Model active parameter count (for Tier 2 FLOPs fallback).
        tokens_in:           Input token count (for Tier 2).
        tokens_out:          Output token count (for Tier 2).
        gpu_model:           GPU model string (for Tier 2 TDP lookup).

    Returns:
        EnergyBreakdown Pydantic model.
    """
    # Apply safe defaults
    runtime_sec = runtime_sec or 0.0
    pue = pue if pue and pue >= 1.0 else 1.2
    num_gpus = num_gpus_used if num_gpus_used and num_gpus_used >= 1 else 1

    # ── Tier 1: Measured power ──────────────────────────────────────────────
    if power_draw_watts is not None and power_draw_watts > 0:
        raw_kwh, total_kwh = _tier1_energy(
            active_power_w=power_draw_watts,
            idle_power_w=idle_power_w,
            runtime_sec=runtime_sec,
            pue=pue,
            num_gpus=num_gpus,
        )
        incremental_w = max(power_draw_watts - idle_power_w, 0.0)
        return EnergyBreakdown(
            event_id=event_id,
            computation_tier="tier1_measured",
            active_power_w=round(power_draw_watts, 4),
            idle_power_w=round(idle_power_w, 4),
            incremental_power_w=round(incremental_w, 4),
            pue_factor=pue,
            num_gpus=num_gpus,
            raw_energy_kwh=round(raw_kwh, 8),
            energy_kwh=round(total_kwh, 8),
        )

    # ── Tier 2: FLOPs estimation ────────────────────────────────────────────
    if active_param_count_b is not None and active_param_count_b > 0:
        est_active_w, raw_kwh, total_kwh = _tier2_energy(
            active_param_count_b=active_param_count_b,
            tokens_in=tokens_in or 0,
            tokens_out=tokens_out or 0,
            gpu_model=gpu_model,
            idle_power_w=idle_power_w,
            runtime_sec=runtime_sec,
            pue=pue,
            num_gpus=num_gpus,
        )
        incremental_w = max(est_active_w - idle_power_w, 0.0)
        return EnergyBreakdown(
            event_id=event_id,
            computation_tier="tier2_flops",
            active_power_w=round(est_active_w, 4),
            idle_power_w=round(idle_power_w, 4),
            incremental_power_w=round(incremental_w, 4),
            pue_factor=pue,
            num_gpus=num_gpus,
            raw_energy_kwh=round(raw_kwh, 8),
            energy_kwh=round(total_kwh, 8),
        )

    # ── No data available ────────────────────────────────────────────────────
    return EnergyBreakdown(
        event_id=event_id,
        computation_tier="unavailable",
        active_power_w=None,
        idle_power_w=round(idle_power_w, 4),
        incremental_power_w=0.0,
        pue_factor=pue,
        num_gpus=num_gpus,
        raw_energy_kwh=0.0,
        energy_kwh=0.0,
    )
