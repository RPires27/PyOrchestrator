from fastapi import FastAPI, Request, Form, Depends, BackgroundTasks, HTTPException # Import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.base import engine, Base, SessionLocal
from app.routes import projects, schedules, runs
from app.services.scheduler import SchedulerService
from app.crud import schedule as crud_schedule
from app.crud import project as crud_project
from app.crud import run as crud_run
from app.schemas import project as schema_project
from app.schemas import schedule as schema_schedule
from app.schemas import run as schema_run
from app.services.executor import execute_script

Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    scheduler_service = SchedulerService(db)
    schedules = crud_schedule.get_schedules(db)
    for schedule in schedules:
        print(f"Scheduling job {schedule.id} with cron: {schedule.cron_schedule}")
        scheduler_service.schedule_job(schedule.id, schedule.project_id, schedule.cron_schedule)
    scheduler_service.start()
    app.state.scheduler = scheduler_service

@app.on_event("shutdown")
def shutdown_event():
    app.state.scheduler.shutdown()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    projects_data = crud_project.get_projects(db)
    schedules_data = crud_schedule.get_schedules(db)
    runs_data = crud_run.get_runs(db, limit=10) # Get last 10 runs
    return templates.TemplateResponse("index.html", {
        "request": request,
        "projects": projects_data,
        "schedules": schedules_data,
        "runs": runs_data
    })

@app.get("/projects/add", response_class=HTMLResponse)
async def add_project_form(request: Request):
    return templates.TemplateResponse("add_project.html", {"request": request})

@app.post("/projects/add", response_class=HTMLResponse)
async def create_project_from_form(
    request: Request,
    name: str = Form(...),
    source_type: str = Form(...),
    source_url: str = Form(None),
    source_path: str = Form(...),
    main_script: str = Form(...),
    arguments: str = Form(None),
    environment_type: str = Form(...),
    db: Session = Depends(get_db)
):
    project_create = schema_project.ProjectCreate(
        name=name,
        source_type=source_type,
        source_url=source_url if source_url else None,
        source_path=source_path,
        main_script=main_script,
        arguments=arguments if arguments else None,
        environment_type=environment_type
    )
    crud_project.create_project(db=db, project=project_create)
    return RedirectResponse(url="/", status_code=303)

@app.get("/projects/{project_id}/edit", response_class=HTMLResponse)
async def edit_project_form(request: Request, project_id: int, db: Session = Depends(get_db)):
    project = crud_project.get_project(db, project_id=project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return templates.TemplateResponse("edit_project.html", {"request": request, "project": project})

@app.post("/projects/{project_id}/edit", response_class=HTMLResponse)
async def update_project_from_form(
    request: Request,
    project_id: int,
    name: str = Form(...),
    source_type: str = Form(...),
    source_url: str = Form(None),
    source_path: str = Form(...),
    main_script: str = Form(...),
    arguments: str = Form(None),
    environment_type: str = Form(...),
    db: Session = Depends(get_db)
):
    project_update = schema_project.ProjectCreate(
        name=name,
        source_type=source_type,
        source_url=source_url if source_url else None,
        source_path=source_path,
        main_script=main_script,
        arguments=arguments if arguments else None,
        environment_type=environment_type
    )
    crud_project.update_project(db=db, project_id=project_id, project=project_update)
    return RedirectResponse(url="/", status_code=303)

@app.post("/projects/{project_id}/delete", response_class=RedirectResponse)
async def delete_project_from_ui(request: Request, project_id: int, db: Session = Depends(get_db)):
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
            
    return RedirectResponse(url="/", status_code=303)

@app.get("/schedules/add", response_class=HTMLResponse)
async def add_schedule_form(request: Request, db: Session = Depends(get_db)):
    projects_data = crud_project.get_projects(db)
    return templates.TemplateResponse("add_schedule.html", {"request": request, "projects": projects_data})

@app.post("/schedules/add", response_class=HTMLResponse)
async def create_schedule_from_form(
    request: Request,
    name: str = Form(...),
    project_id: int = Form(...),
    cron_schedule: str = Form(...),
    db: Session = Depends(get_db)
):
    schedule_create = schema_schedule.ScheduleCreate(
        name=name,
        project_id=project_id,
        cron_schedule=cron_schedule
    )
    db_schedule = crud_schedule.create_schedule(db=db, schedule=schedule_create)
    
    # Add to scheduler immediately
    scheduler: SchedulerService = request.app.state.scheduler
    scheduler.schedule_job(db_schedule.id, db_schedule.project_id, db_schedule.cron_schedule)

    return RedirectResponse(url="/", status_code=303)

@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: int, db: Session = Depends(get_db)):
    project = crud_project.get_project(db, project_id=project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return templates.TemplateResponse("project_detail.html", {"request": request, "project": project})

@app.post("/projects/{project_id}/run", response_class=RedirectResponse)
async def run_project_now(project_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run_create = schema_run.RunCreate(project_id=project_id)
    db_run = crud_run.create_run(db=db, run=run_create)
    background_tasks.add_task(execute_script, db, db_run.id)
    return RedirectResponse(url=f"/runs/{db_run.id}", status_code=303)

@app.get("/schedules/{schedule_id}", response_class=HTMLResponse)
async def schedule_detail(request: Request, schedule_id: int, db: Session = Depends(get_db)):
    schedule = crud_schedule.get_schedule(db, schedule_id=schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return templates.TemplateResponse("schedule_detail.html", {"request": request, "schedule": schedule})

@app.get("/runs/{run_id}", response_class=HTMLResponse)
async def run_detail(request: Request, run_id: int, db: Session = Depends(get_db)):
    run = crud_run.get_run(db, run_id=run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return templates.TemplateResponse("run_detail.html", {"request": request, "run": run})

# Include the routers after the add routes
app.include_router(projects.router)
app.include_router(schedules.router)
app.include_router(runs.router)