from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session

from .collectors.carbon_api import get_carbon_intensity


from .database.db import init_database,get_database
from .models.model import InferenceEvent,HardwareSnapshot
from .schemas.schema import EventCreate,EventOut,HardwareSnapshotCreate,HardwareSnapshotOut



from .collectors.hardware_data import get_cpu_power_estimate, get_gpu_power_draw, get_gpu_util



app=FastAPI(title="EcoGen-AI Ingestion Layer")


@app.on_event("startup")
def on_startup():
    init_database()


@app.post("/ingest/event",response_model=EventOut)
def log_event(event:EventCreate,db:Session=Depends(get_database)):
    db_event=InferenceEvent(**event.dict())
    if db_event.region:
        db_event.carbon_intensity=get_carbon_intensity(db_event.region)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@app.post("/ingest/hardware",response_model=HardwareSnapshotOut)
def log_hardware(snap:HardwareSnapshotCreate,db:Session=Depends(get_database)):
    db_snap=HardwareSnapshot(**snap.dict())
    db.add(db_snap)
    db.commit()
    db.refresh(db_snap)
    return db_snap



@app.post("/ingest/hardware/auto",response_model=HardwareSnapshotOut)
def log_hardware_auto(device_id:str,db:Session=Depends(get_database)):

    gpu_power=get_gpu_power_draw()
    power=gpu_power if gpu_power is not None else get_cpu_power_estimate()

    db_snap=HardwareSnapshot(
        device_id=device_id,
        power_draw_watts=power,
        gpu_util_pct=get_gpu_util(),
    )
    db.add(db_snap)
    db.commit()
    db.refresh(db_snap)
    return db_snap