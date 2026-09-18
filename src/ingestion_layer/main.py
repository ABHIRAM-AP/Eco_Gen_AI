from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session


from .database.db import init_database,get_database
from .models.model import InferenceEvent,HardwareSnapshot
from .schemas.schema import EventCreate,EventOut,HardwareSnapshotCreate,HardwareSnapshotOut


app=FastAPI(title="EcoGen-AI Ingestion Layer")


@app.on_event("startup")
def on_startup():
    init_database()


@app.post("/ingest/event",response_model=EventOut)
def log_event(event:EventCreate,db:Session=Depends(get_database)):
    db_event=InferenceEvent(**event.dict())
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