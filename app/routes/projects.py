from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.crud import project as crud_project
from app.schemas import project as schema_project
from app.database.base import SessionLocal

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