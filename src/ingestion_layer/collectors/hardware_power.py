"""
Compatibility module re-exporting hardware_data components for collectors/hardware_power.
"""
from .hardware_data import (
    get_cpu_power_estimate,
    get_gpu_power_draw,
    get_gpu_util,
    get_idle_power_baseline,
    sample_idle_power_baseline,
    sample_idle_baseline_power,
    sample_idle_power,
    post_hardware_snapshot,
)

__all__ = [
    "get_cpu_power_estimate",
    "get_gpu_power_draw",
    "get_gpu_util",
    "get_idle_power_baseline",
    "sample_idle_power_baseline",
    "sample_idle_baseline_power",
    "sample_idle_power",
    "post_hardware_snapshot",
]
