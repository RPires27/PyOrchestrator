from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.crud import schedule as crud_schedule
from app.schemas import schedule as schema_schedule
from app.database.base import SessionLocal
from app.services.scheduler import SchedulerService

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
def create_schedule(request: Request, schedule: schema_schedule.ScheduleCreate, db: Session = Depends(get_db)):
    db_schedule = crud_schedule.create_schedule(db=db, schedule=schedule)
    scheduler: SchedulerService = request.app.state.scheduler
    scheduler.schedule_job(db_schedule.id, db_schedule.project_id, db_schedule.cron_schedule)
    return db_schedule

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

@router.put("/{schedule_id}", response_model=schema_schedule.Schedule)
def update_schedule(request: Request, schedule_id: int, schedule: schema_schedule.ScheduleCreate, db: Session = Depends(get_db)):
    db_schedule = crud_schedule.update_schedule(db, schedule_id=schedule_id, schedule=schedule)
    if db_schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    scheduler: SchedulerService = request.app.state.scheduler
    try:
        scheduler.scheduler.remove_job(str(schedule_id))
    except Exception as e:
        print(f"Error removing job: {e}")
    scheduler.schedule_job(db_schedule.id, db_schedule.project_id, db_schedule.cron_schedule)
    
    return db_schedule

@router.delete("/{schedule_id}", response_model=schema_schedule.Schedule)
def delete_schedule(request: Request, schedule_id: int, db: Session = Depends(get_db)):
    db_schedule = crud_schedule.delete_schedule(db, schedule_id=schedule_id)
    if db_schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    scheduler: SchedulerService = request.app.state.scheduler
    try:
        scheduler.scheduler.remove_job(str(schedule_id))
    except Exception as e:
        print(f"Error removing job: {e}")
    
    return db_schedule