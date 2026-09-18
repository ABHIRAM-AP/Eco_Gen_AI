import psutil
import subprocess


def get_cpu_power_estimate()->float:
    cpu_percent=psutil.cpu_percent(interval=0.5)
    assumed_tdp_watts=65
    return round((cpu_percent/100) *assumed_tdp_watts,2)

def get_gpu_power_draw()->float|None:
    try:
        result=subprocess.run(
            ["nvidia-smi","--query-gpu=power.draw","--format=csv,nonheader,nounits"],
            capture_output=True,text=True,timeout=5
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