from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .collectors.carbon_api import get_carbon_intensity
from .database.db import init_database, get_database
from .models.model import InferenceEvent, HardwareSnapshot
from .schemas.schema import EventCreate, EventOut, HardwareSnapshotCreate, HardwareSnapshotOut
from .collectors.hardware_data import (
    get_cpu_power_estimate,
    get_gpu_power_draw,
    get_gpu_util,
    get_idle_power_baseline,
)


app = FastAPI(title="EcoGen-AI Ingestion Layer")


@app.on_event("startup")
def on_startup():
    init_database()


@app.post("/ingest/event", response_model=EventOut)
def log_event(event: EventCreate, db: Session = Depends(get_database)):
    event_dict = event.dict()
    # Apply model-level defaults if None
    if event_dict.get("pue") is None:
        event_dict["pue"] = 1.2
    if event_dict.get("num_gpus_used") is None:
        event_dict["num_gpus_used"] = 1
    if event_dict.get("batch_size") is None:
        event_dict["batch_size"] = 1

    db_event = InferenceEvent(**event_dict)
    if db_event.region:
        db_event.carbon_intensity = get_carbon_intensity(db_event.region)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@app.post("/ingest/hardware", response_model=HardwareSnapshotOut)
def log_hardware(snap: HardwareSnapshotCreate, db: Session = Depends(get_database)):
    db_snap = HardwareSnapshot(**snap.dict())
    db.add(db_snap)
    db.commit()
    db.refresh(db_snap)
    return db_snap


@app.post("/ingest/hardware/auto", response_model=HardwareSnapshotOut)
def log_hardware_auto(
    device_id: str,
    idle_power_baseline_w: Optional[float] = None,
    sample_idle: bool = False,
    db: Session = Depends(get_database),
):
    gpu_power = get_gpu_power_draw()
    power = gpu_power if gpu_power is not None else get_cpu_power_estimate()

    if idle_power_baseline_w is None and sample_idle:
        idle_power_baseline_w = get_idle_power_baseline(samples=2, interval_sec=0.2)

    db_snap = HardwareSnapshot(
        device_id=device_id,
        power_draw_watts=power,
        gpu_util_pct=get_gpu_util(),
        idle_power_baseline_w=idle_power_baseline_w,
    )
    db.add(db_snap)
    db.commit()
    db.refresh(db_snap)
    return db_snap


@app.get("/events", response_model=List[EventOut])
def get_events(limit: int = 50, db: Session = Depends(get_database)):
    return (
        db.query(InferenceEvent)
        .order_by(InferenceEvent.timestamp.desc())
        .limit(limit)
        .all()
    )


@app.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_database)):
    event = db.query(InferenceEvent).filter(InferenceEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.get("/hardware", response_model=List[HardwareSnapshotOut])
def get_hardware(limit: int = 50, db: Session = Depends(get_database)):
    return (
        db.query(HardwareSnapshot)
        .order_by(HardwareSnapshot.timestamp.desc())
        .limit(limit)
        .all()
    )


@app.get("/hardware/{snapshot_id}", response_model=HardwareSnapshotOut)
def get_hardware_snapshot(snapshot_id: int, db: Session = Depends(get_database)):
    snapshot = db.query(HardwareSnapshot).filter(HardwareSnapshot.id == snapshot_id).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Hardware snapshot not found")
    return snapshot