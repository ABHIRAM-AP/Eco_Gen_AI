import psutil
import subprocess
import time


def get_cpu_power_estimate() -> float:
    cpu_percent = psutil.cpu_percent(interval=0.5)
    assumed_tdp_watts = 65
    return round((cpu_percent / 100) * assumed_tdp_watts, 2)


def get_gpu_power_draw() -> float | None:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        return float(result.stdout.strip().split("\n")[0])
    except Exception:
        return None


def get_gpu_util() -> float | None:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        return float(result.stdout.strip().split("\n")[0])
    except Exception:
        return None


def get_idle_power_baseline(samples: int = 4, interval_sec: float = 0.5) -> float:
    """
    Samples power draw (GPU if available, otherwise CPU estimate) multiple times
    over a period when no request is active, returning the average baseline power in watts.
    """
    readings: list[float] = []
    for _ in range(max(1, samples)):
        gpu_power = get_gpu_power_draw()
        if gpu_power is not None:
            readings.append(gpu_power)
        else:
            readings.append(get_cpu_power_estimate())
        if interval_sec > 0 and _ < samples - 1:
            time.sleep(interval_sec)

    if not readings:
        return 0.0
    return round(sum(readings) / len(readings), 2)