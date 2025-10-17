from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.crud import project as crud_project
from app.schemas import project as schema_project
from app.database.base import SessionLocal
from app.services.scheduler import SchedulerService
from app.crud import schedule as crud_schedule

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schema_project.Project)
def create_project(project: schema_project.ProjectCreate, db: Session = Depends(get_db)):
    return crud_project.create_project(db=db, project=project)

@router.get("/", response_model=list[schema_project.Project])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = crud_project.get_projects(db, skip=skip, limit=limit)
    return projects

@router.get("/{project_id}", response_model=schema_project.Project)
def read_project(project_id: int, db: Session = Depends(get_db)):
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

@router.put("/{project_id}", response_model=schema_project.Project)
def update_project(project_id: int, project: schema_project.ProjectCreate, db: Session = Depends(get_db)):
    db_project = crud_project.update_project(db, project_id=project_id, project=project)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

@router.delete("/{project_id}", response_model=schema_project.Project)
def delete_project(request: Request, project_id: int, db: Session = Depends(get_db)):
    # Get schedules associated with the project before deleting the project
    schedules_to_delete = crud_schedule.get_schedules_by_project_id(db, project_id=project_id)
    
    db_project = crud_project.delete_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scheduler: SchedulerService = request.app.state.scheduler
    for schedule in schedules_to_delete:
        try:
            scheduler.remove_job(schedule.id)
        except Exception as e:
            print(f"Error removing job {schedule.id} from scheduler: {e}")
            
    return db_project
