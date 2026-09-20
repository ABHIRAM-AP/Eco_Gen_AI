from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EventCreate(BaseModel):
    model_name: str
    task_type: str
    tokens_in: int = 0
    tokens_out: int = 0
    runtime_sec: float
    region: Optional[str] = None
    provider: Optional[str] = None
    pue: Optional[float] = 1.2
    gpu_model: Optional[str] = None
    num_gpus_used: Optional[int] = 1
    batch_size: Optional[int] = 1
    cost_usd: Optional[float] = None
    department: Optional[str] = None
    use_case: Optional[str] = None
    param_count_b: Optional[float] = None
    active_param_count_b: Optional[float] = None


class EventOut(EventCreate):
    id: int
    power_draw_watts: Optional[float] = None
    carbon_intensity: Optional[float] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class HardwareSnapshotCreate(BaseModel):
    device_id: str
    power_draw_watts: float
    gpu_util_pct: Optional[float] = None
    temp_c: Optional[float] = None
    idle_power_baseline_w: Optional[float] = None
    hardware_install_date: Optional[datetime] = None

class HardwareSnapshotOut(HardwareSnapshotCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True