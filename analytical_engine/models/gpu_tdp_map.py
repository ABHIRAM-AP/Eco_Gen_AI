"""
GPU TDP and Embodied Carbon Registry
-------------------------------------
Sources:
  - TDP values: NVIDIA product datasheets & GPU specifications
  - Embodied carbon: Dell & HP sustainability reports, GreenPixie GPU lifecycle estimates
  - Lifespan assumptions: industry standard (5 yrs datacenter, 4 yrs consumer)

All TDP values are in Watts (peak / rated).
All embodied carbon values are in grams of CO2-equivalent (gCO2eq).
"""

from typing import Optional

# ---------------------------------------------------------------------------
# GPU TDP Map (Watts — peak rated power)
# ---------------------------------------------------------------------------
GPU_TDP_MAP: dict[str, float] = {
    # NVIDIA H-Series (Hopper) — Datacenter
    "h100": 700.0,
    "h100 sxm5": 700.0,
    "h100 pcie": 350.0,
    "h100-sxm5-80gb": 700.0,
    "h100-pcie-80gb": 350.0,
    "h200": 700.0,
    "h200 sxm5": 700.0,

    # NVIDIA A-Series (Ampere) — Datacenter
    "a100": 400.0,
    "a100-sxm4-80gb": 400.0,
    "a100-sxm4-40gb": 400.0,
    "a100-pcie-80gb": 300.0,
    "a100-pcie-40gb": 250.0,
    "a10": 150.0,
    "a10g": 150.0,
    "a30": 165.0,
    "a40": 300.0,
    "a6000": 300.0,

    # NVIDIA L-Series (Ada Lovelace) — Datacenter
    "l4": 72.0,
    "l40": 300.0,
    "l40s": 350.0,

    # NVIDIA V-Series (Volta) — Datacenter (legacy)
    "v100": 300.0,
    "v100-sxm2-32gb": 300.0,
    "v100-pcie-32gb": 250.0,

    # NVIDIA RTX 40-Series — Consumer / Workstation
    "rtx 4090": 450.0,
    "rtx 4080": 320.0,
    "rtx 4080 super": 320.0,
    "rtx 4070 ti": 285.0,
    "rtx 4070 ti super": 285.0,
    "rtx 4070": 200.0,
    "rtx 4060 ti": 160.0,
    "rtx 4060": 115.0,

    # NVIDIA RTX 30-Series — Consumer (legacy)
    "rtx 3090": 350.0,
    "rtx 3090 ti": 450.0,
    "rtx 3080": 320.0,
    "rtx 3080 ti": 350.0,
    "rtx 3070": 220.0,
    "rtx 3060 ti": 200.0,
    "rtx 3060": 170.0,

    # AMD Instinct — Datacenter
    "mi300x": 750.0,
    "mi250x": 500.0,
    "mi250": 500.0,
    "mi100": 300.0,

    # Generic fallback — used when model is unknown
    "unknown": 300.0,
    "none": 65.0,   # CPU-only fallback
}

# ---------------------------------------------------------------------------
# GPU Embodied Carbon Map (gCO2eq — full lifecycle manufacturing)
# Includes: fabrication, packaging, transport, materials
# ---------------------------------------------------------------------------
GPU_EMBODIED_MAP: dict[str, dict] = {
    # NVIDIA H-Series
    "h100": {"manufacturing_gco2eq": 143_000.0, "lifespan_years": 5},
    "h100-sxm5-80gb": {"manufacturing_gco2eq": 143_000.0, "lifespan_years": 5},
    "h100-pcie-80gb": {"manufacturing_gco2eq": 120_000.0, "lifespan_years": 5},
    "h200": {"manufacturing_gco2eq": 160_000.0, "lifespan_years": 5},

    # NVIDIA A-Series
    "a100": {"manufacturing_gco2eq": 97_000.0, "lifespan_years": 5},
    "a100-sxm4-80gb": {"manufacturing_gco2eq": 97_000.0, "lifespan_years": 5},
    "a100-pcie-80gb": {"manufacturing_gco2eq": 80_000.0, "lifespan_years": 5},
    "a10g": {"manufacturing_gco2eq": 40_000.0, "lifespan_years": 5},
    "a40": {"manufacturing_gco2eq": 60_000.0, "lifespan_years": 5},
    "a6000": {"manufacturing_gco2eq": 62_000.0, "lifespan_years": 5},

    # NVIDIA L-Series
    "l4": {"manufacturing_gco2eq": 25_000.0, "lifespan_years": 5},
    "l40s": {"manufacturing_gco2eq": 65_000.0, "lifespan_years": 5},

    # NVIDIA V-Series
    "v100": {"manufacturing_gco2eq": 70_000.0, "lifespan_years": 5},

    # NVIDIA RTX 40-Series
    "rtx 4090": {"manufacturing_gco2eq": 72_000.0, "lifespan_years": 4},
    "rtx 4080": {"manufacturing_gco2eq": 55_000.0, "lifespan_years": 4},
    "rtx 4070 ti": {"manufacturing_gco2eq": 45_000.0, "lifespan_years": 4},
    "rtx 4070": {"manufacturing_gco2eq": 38_000.0, "lifespan_years": 4},
    "rtx 4060 ti": {"manufacturing_gco2eq": 30_000.0, "lifespan_years": 4},
    "rtx 4060": {"manufacturing_gco2eq": 24_000.0, "lifespan_years": 4},

    # NVIDIA RTX 30-Series
    "rtx 3090": {"manufacturing_gco2eq": 65_000.0, "lifespan_years": 4},
    "rtx 3080": {"manufacturing_gco2eq": 55_000.0, "lifespan_years": 4},
    "rtx 3070": {"manufacturing_gco2eq": 42_000.0, "lifespan_years": 4},
    "rtx 3060 ti": {"manufacturing_gco2eq": 34_000.0, "lifespan_years": 4},

    # AMD Instinct
    "mi300x": {"manufacturing_gco2eq": 180_000.0, "lifespan_years": 5},
    "mi250x": {"manufacturing_gco2eq": 120_000.0, "lifespan_years": 5},

    # Fallback
    "unknown": {"manufacturing_gco2eq": 97_000.0, "lifespan_years": 5},
    "none": {"manufacturing_gco2eq": 5_000.0, "lifespan_years": 5},   # CPU
}

# Peak theoretical FLOPS (FP16/BF16) in TFLOPS — for Tier 2 estimation
GPU_PEAK_TFLOPS_MAP: dict[str, float] = {
    "h100": 1979.0,
    "h100-sxm5-80gb": 1979.0,
    "h100-pcie-80gb": 1513.0,
    "h200": 1979.0,
    "a100": 312.0,
    "a100-sxm4-80gb": 312.0,
    "a100-pcie-80gb": 312.0,
    "a10g": 125.0,
    "l4": 121.0,
    "l40s": 733.0,
    "v100": 125.0,
    "rtx 4090": 165.0,
    "rtx 4080": 97.0,
    "rtx 3090": 71.0,
    "rtx 3080": 59.0,
    "mi300x": 1307.0,
    "mi250x": 383.0,
    "unknown": 312.0,
    "none": 10.0,   # CPU approximate
}


def _normalize_key(gpu_model: Optional[str]) -> str:
    """Normalize a GPU model string to a lowercase lookup key."""
    if not gpu_model:
        return "unknown"
    return gpu_model.strip().lower()


def get_gpu_tdp(gpu_model: Optional[str]) -> float:
    """
    Return rated TDP in Watts for a given GPU model string.
    Falls back to 'unknown' (300W) if not found.
    """
    key = _normalize_key(gpu_model)
    if key in GPU_TDP_MAP:
        return GPU_TDP_MAP[key]
    # Partial match — e.g. "NVIDIA H100 SXM5" → "h100 sxm5"
    for known_key, tdp in GPU_TDP_MAP.items():
        if known_key in key or key in known_key:
            return tdp
    return GPU_TDP_MAP["unknown"]


def get_gpu_embodied_carbon(gpu_model: Optional[str]) -> dict:
    """
    Return embodied carbon metadata dict:
        {"manufacturing_gco2eq": float, "lifespan_years": int}
    Falls back to A100 figures if GPU is unknown.
    """
    key = _normalize_key(gpu_model)
    if key in GPU_EMBODIED_MAP:
        return GPU_EMBODIED_MAP[key]
    for known_key, data in GPU_EMBODIED_MAP.items():
        if known_key in key or key in known_key:
            return data
    return GPU_EMBODIED_MAP["unknown"]


def get_gpu_peak_tflops(gpu_model: Optional[str]) -> float:
    """
    Return peak FP16/BF16 TFLOPS for a GPU.
    Used in Tier 2 FLOPs-based energy estimation.
    """
    key = _normalize_key(gpu_model)
    if key in GPU_PEAK_TFLOPS_MAP:
        return GPU_PEAK_TFLOPS_MAP[key]
    for known_key, tflops in GPU_PEAK_TFLOPS_MAP.items():
        if known_key in key or key in known_key:
            return tflops
    return GPU_PEAK_TFLOPS_MAP["unknown"]
