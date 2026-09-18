from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models.model import Base


DB_URL="sqlite:///./ecogen.db"

engine=create_engine(DB_URL,connect_args={"check_same_thread":False})
SessionLocal=sessionmaker(bind=engine)

def init_database():
    Base.metadata.create_all(bind=engine)

def get_database():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()