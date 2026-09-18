from sqlalchemy import Column,Integer,String,Float,DateTime
from sqlalchemy.orm import declarative_base

from datetime import datetime


Base=declarative_base()


class InferenceEvent(Base):
    __tablename__="inference_events"

    id=Column(Integer,primary_key=True,index=True)
    model_name=Column(String,nullable=False)
    task_type=Column(String)
    tokens_in=Column(Integer,default=0)
    tokens_out=Column(Integer,default=0)
    runtime_sec=Column(Float)
    power_draw_watts=Column(Float,nullable=True)
    carbon_intensity=Column(Float,nullable=True)
    region=Column(String,nullable=True)
    timestamp=Column(DateTime,default=datetime.utcnow)


class HardwareSnapshot(Base):
    __tablename__="hardware_snapshots"

    id=Column(Integer,primary_key=True,index=True)
    device_id=Column(String)
    power_draw_watts=Column(Float)
    gpu_util_pct=Column(Float,nullable=True)
    temp_c=Column(Float,nullable=True)
    timestamp=Column(DateTime,default=datetime.utcnow)