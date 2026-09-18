from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EventCreate(BaseModel):
    model_name:str
    task_type:str
    tokens_in:int=0
    tokens_out:int=0
    runtime_sec:float
    region:Optional[str]=None


class EventOut(EventCreate):
    id:int
    power_draw_watts:Optional[float]=None
    carbon_intensity:Optional[float]=None
    timestamp:datetime

    class Config:
        from_attributes=True


class HardwareSnapshotCreate(BaseModel):
    device_id:str
    power_draw_watts:float
    gpu_util_pct:Optional[float]=None
    temp_c:Optional[float]=None

class HardwareSnapshotOut(HardwareSnapshotCreate):
    id:int
    timestamp:datetime

    class Config:
        from_attributes=True