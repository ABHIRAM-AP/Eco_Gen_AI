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


# Function aliases for flexibility and convenience
sample_idle_power_baseline = get_idle_power_baseline
sample_idle_baseline_power = get_idle_power_baseline
sample_idle_power = get_idle_power_baseline


def post_hardware_snapshot(
    device_id: str,
    power_draw_watts: float | None = None,
    idle_power_baseline_w: float | None = None,
    sample_idle: bool = False,
    gpu_util_pct: float | None = None,
    temp_c: float | None = None,
    hardware_install_date=None,
    api_url: str = "http://127.0.0.1:8000/ingest/hardware",
):
    """
    Captures or accepts hardware power metrics (including idle baseline) and posts them to /ingest/hardware.
    """
    import requests

    if power_draw_watts is None:
        gpu_power = get_gpu_power_draw()
        power_draw_watts = gpu_power if gpu_power is not None else get_cpu_power_estimate()

    if gpu_util_pct is None:
        gpu_util_pct = get_gpu_util()

    if idle_power_baseline_w is None and sample_idle:
        idle_power_baseline_w = get_idle_power_baseline()

    payload = {
        "device_id": device_id,
        "power_draw_watts": power_draw_watts,
        "gpu_util_pct": gpu_util_pct,
        "temp_c": temp_c,
        "idle_power_baseline_w": idle_power_baseline_w,
    }
    if hardware_install_date is not None:
        payload["hardware_install_date"] = (
            hardware_install_date.isoformat()
            if hasattr(hardware_install_date, "isoformat")
            else str(hardware_install_date)
        )

    resp = requests.post(api_url, json=payload, timeout=5)
    resp.raise_for_status()
    return resp.json()