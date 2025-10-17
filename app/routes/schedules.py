from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.crud import schedule as crud_schedule
from app.schemas import schedule as schema_schedule
from app.database.base import SessionLocal

router = APIRouter(
    prefix="/schedules",
    tags=["schedules"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schema_schedule.Schedule)
def create_schedule(schedule: schema_schedule.ScheduleCreate, db: Session = Depends(get_db)):
    return crud_schedule.create_schedule(db=db, schedule=schedule)

@router.get("/", response_model=list[schema_schedule.Schedule])
def read_schedules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    schedules = crud_schedule.get_schedules(db, skip=skip, limit=limit)
    return schedules

@router.get("/{schedule_id}", response_model=schema_schedule.Schedule)
def read_schedule(schedule_id: int, db: Session = Depends(get_db)):
    db_schedule = crud_schedule.get_schedule(db, schedule_id=schedule_id)
    if db_schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return db_schedule
