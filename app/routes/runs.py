from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.crud import run as crud_run
from app.schemas import run as schema_run
from app.database.base import SessionLocal

router = APIRouter(
    prefix="/runs",
    tags=["runs"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schema_run.Run)
def create_run(run: schema_run.RunCreate, db: Session = Depends(get_db)):
    return crud_run.create_run(db=db, run=run)

@router.get("/", response_model=list[schema_run.Run])
def read_runs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    runs = crud_run.get_runs(db, skip=skip, limit=limit)
    return runs

@router.get("/{run_id}", response_model=schema_run.Run)
def read_run(run_id: int, db: Session = Depends(get_db)):
    db_run = crud_run.get_run(db, run_id=run_id)
    if db_run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return db_run

@router.put("/{run_id}", response_model=schema_run.Run)
def update_run(run_id: int, status: str, log_output: str | None = None, db: Session = Depends(get_db)):
    db_run = crud_run.update_run_status(db, run_id, status, log_output)
    if db_run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return db_run
