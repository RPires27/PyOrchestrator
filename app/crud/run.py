from sqlalchemy.orm import Session
from app.models.run import Run
from app.schemas.run import RunCreate
from datetime import datetime

def get_run(db: Session, run_id: int):
    return db.query(Run).filter(Run.id == run_id).first()

def get_runs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Run).offset(skip).limit(limit).all()

def create_run(db: Session, run: RunCreate):
    db_run = Run(**run.model_dump())
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

def update_run_status(db: Session, run_id: int, status: str, log_output: str = None):
    db_run = db.query(Run).filter(Run.id == run_id).first()
    if db_run:
        db_run.status = status
        if status in ["completed", "failed"]:
            db_run.end_time = datetime.now()
        if log_output:
            db_run.log_output = log_output
        db.commit()
        db.refresh(db_run)
    return db_run
