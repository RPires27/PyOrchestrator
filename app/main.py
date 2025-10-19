from fastapi import FastAPI, Request, Form, Depends, BackgroundTasks, HTTPException # Import HTTPException
from fastapi.staticfiles import StaticFiles # Import StaticFiles
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
from app.services.executor import execute_script, sync_project_dependencies # Import sync_project_dependencies
import math # Import math for ceil
from app.core.logging_config import setup_logging # Import setup_logging
from app.core.utils import get_timezones # Import get_timezones
from typing import List # Import List

# Setup logging as early as possible
logger = setup_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

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
        logger.info(f"Scheduling job {schedule.id} with cron: {schedule.cron_schedule} in timezone {schedule.timezone}")
        scheduler_service.schedule_job(schedule.id, schedule.project_id, schedule.cron_schedule, schedule.timezone)
    scheduler_service.start()
    app.state.scheduler = scheduler_service
    logger.info("Application startup complete. Scheduler started.")

@app.on_event("shutdown")
def shutdown_event():
    app.state.scheduler.shutdown()
    logger.info("Application shutdown complete. Scheduler stopped.")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    projects_data = crud_project.get_projects(db)
    logger.info("Dashboard accessed.")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "projects": projects_data
    })

@app.get("/projects/add", response_class=HTMLResponse)
async def add_project_form(request: Request):
    logger.info("Add project form requested.")
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
    logger.info(f"Project '{name}' created.")
    return RedirectResponse(url="/", status_code=303)

@app.get("/projects/{project_id}/edit", response_class=HTMLResponse)
async def edit_project_form(request: Request, project_id: int, db: Session = Depends(get_db)):
    project = crud_project.get_project(db, project_id=project_id)
    if project is None:
        logger.warning(f"Attempted to edit non-existent project with ID: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    logger.info(f"Edit project form requested for project ID: {project_id}")
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
    logger.info(f"Project ID {project_id} updated to '{name}'.")
    return RedirectResponse(url="/", status_code=303)

@app.post("/projects/{project_id}/delete", response_class=RedirectResponse)
async def delete_project_from_ui(request: Request, project_id: int, db: Session = Depends(get_db)):
    schedules_to_delete = crud_schedule.get_schedules_by_project_id(db, project_id=project_id)
    
    db_project = crud_project.delete_project(db, project_id=project_id)
    if db_project is None:
        logger.warning(f"Attempted to delete non-existent project with ID: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    
    scheduler: SchedulerService = request.app.state.scheduler
    for schedule in schedules_to_delete:
        try:
            scheduler.remove_job(schedule.id)
            logger.info(f"Removed schedule ID {schedule.id} from scheduler due to project deletion.")
        except Exception as e:
            logger.error(f"Error removing job {schedule.id} from scheduler during project deletion: {e}")
            
    logger.info(f"Project ID {project_id} deleted.")
    return RedirectResponse(url="/", status_code=303)

@app.post("/projects/{project_id}/sync-dependencies", response_class=RedirectResponse)
async def sync_dependencies_for_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    project = crud_project.get_project(db, project_id=project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    background_tasks.add_task(sync_project_dependencies, project.source_path, project.environment_type)
    logger.info(f"Triggered dependency sync for project ID: {project_id}")
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

@app.get("/schedules/add", response_class=HTMLResponse)
async def add_schedule_form(request: Request, db: Session = Depends(get_db)):
    projects_data = crud_project.get_projects(db)
    timezones = get_timezones()
    logger.info("Add schedule form requested.")
    return templates.TemplateResponse("add_schedule.html", {"request": request, "projects": projects_data, "timezones": timezones})

@app.post("/schedules/add", response_class=HTMLResponse)
async def create_schedule_from_form(
    request: Request,
    name: str = Form(...),
    project_id: int = Form(...),
    timezone: str = Form("UTC"),
    schedule_type: str = Form(...),
    run_days: List[str] = Form([]),
    run_time: str = Form(None),
    cron_schedule: str = Form(None),
    db: Session = Depends(get_db)
):
    final_cron_schedule = cron_schedule
    if schedule_type == "simple":
        if not run_time or not run_days:
            raise HTTPException(status_code=400, detail="Run time and at least one run day are required for simple schedules.")
        hour, minute = run_time.split(':')
        days_of_week = ",".join(run_days)
        final_cron_schedule = f"{minute} {hour} * * {days_of_week}"
    
    schedule_create = schema_schedule.ScheduleCreate(
        name=name,
        project_id=project_id,
        cron_schedule=final_cron_schedule,
        timezone=timezone,
        schedule_type=schedule_type,
        run_days=",".join(run_days) if run_days else None,
        run_time=run_time
    )
    db_schedule = crud_schedule.create_schedule(db=db, schedule=schedule_create)
    
    scheduler: SchedulerService = request.app.state.scheduler
    scheduler.schedule_job(db_schedule.id, db_schedule.project_id, db_schedule.cron_schedule, db_schedule.timezone)
    logger.info(f"Schedule '{name}' created with cron: {final_cron_schedule}")

    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

@app.get("/schedules/{schedule_id}/edit", response_class=HTMLResponse)
async def edit_schedule_form(request: Request, schedule_id: int, db: Session = Depends(get_db)):
    schedule = crud_schedule.get_schedule(db, schedule_id=schedule_id)
    if schedule is None:
        logger.warning(f"Attempted to edit non-existent schedule with ID: {schedule_id}")
        raise HTTPException(status_code=404, detail="Schedule not found")
    projects_data = crud_project.get_projects(db)
    timezones = get_timezones()
    logger.info(f"Edit schedule form requested for schedule ID: {schedule_id}")
    return templates.TemplateResponse("edit_schedule.html", {"request": request, "schedule": schedule, "projects": projects_data, "timezones": timezones})

@app.post("/schedules/{schedule_id}/edit", response_class=HTMLResponse)
async def update_schedule_from_form(
    request: Request,
    schedule_id: int,
    name: str = Form(...),
    project_id: int = Form(...),
    timezone: str = Form("UTC"),
    schedule_type: str = Form(...),
    run_days: List[str] = Form([]),
    run_time: str = Form(None),
    cron_schedule: str = Form(None),
    db: Session = Depends(get_db)
):
    final_cron_schedule = cron_schedule
    if schedule_type == "simple":
        if not run_time or not run_days:
            raise HTTPException(status_code=400, detail="Run time and at least one run day are required for simple schedules.")
        hour, minute = run_time.split(':')
        days_of_week = ",".join(run_days)
        final_cron_schedule = f"{minute} {hour} * * {days_of_week}"

    schedule_update = schema_schedule.ScheduleCreate(
        name=name,
        project_id=project_id,
        cron_schedule=final_cron_schedule,
        timezone=timezone,
        schedule_type=schedule_type,
        run_days=",".join(run_days) if run_days else None,
        run_time=run_time
    )
    db_schedule = crud_schedule.update_schedule(db, schedule_id=schedule_id, schedule=schedule_update)
    if db_schedule is None:
        logger.warning(f"Attempted to update non-existent schedule with ID: {schedule_id}")
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    scheduler: SchedulerService = request.app.state.scheduler
    try:
        scheduler.remove_job(db_schedule.id)
        logger.info(f"Removed old job for schedule ID {db_schedule.id} from scheduler.")
    except Exception as e:
        logger.error(f"Error removing old job for schedule ID {db_schedule.id} from scheduler: {e}")
    scheduler.schedule_job(db_schedule.id, db_schedule.project_id, db_schedule.cron_schedule, db_schedule.timezone)
    logger.info(f"Schedule ID {schedule_id} updated and re-added to scheduler with cron: {final_cron_schedule}")

    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)

@app.post("/schedules/{schedule_id}/delete", response_class=RedirectResponse)
async def delete_schedule_from_ui(request: Request, schedule_id: int, db: Session = Depends(get_db)):
    db_schedule = crud_schedule.delete_schedule(db, schedule_id=schedule_id)
    if db_schedule is None:
        logger.warning(f"Attempted to delete non-existent schedule with ID: {schedule_id}")
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    scheduler: SchedulerService = request.app.state.scheduler
    try:
        scheduler.remove_job(db_schedule.id)
        logger.info(f"Removed schedule ID {db_schedule.id} from scheduler.")
    except Exception as e:
        logger.error(f"Error removing job {db_schedule.id} from scheduler: {e}")
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/schedules/{schedule_id}/run", response_class=RedirectResponse)
async def run_schedule_now(schedule_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    schedule = crud_schedule.get_schedule(db, schedule_id=schedule_id)
    if schedule is None:
        logger.warning(f"Attempted to run non-existent schedule with ID: {schedule_id}")
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    run_create = schema_run.RunCreate(project_id=schedule.project_id, schedule_id=schedule.id)
    db_run = crud_run.create_run(db=db, run=run_create)
    background_tasks.add_task(execute_script, db, db_run.id)
    logger.info(f"Manually triggered run for schedule ID {schedule_id}. Run ID: {db_run.id}")
    return RedirectResponse(url=f"/runs/{db_run.id}", status_code=303)

@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    page: int = 1,
    page_size: int = 10 # Default page size
):
    project = crud_project.get_project(db, project_id=project_id)
    if project is None:
        logger.warning(f"Attempted to view details of non-existent project with ID: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    
    schedules_data = crud_schedule.get_schedules_by_project_id(db, project_id=project_id)
    
    total_runs = crud_run.get_runs_count_by_project_id(db, project_id=project_id)
    runs_data = crud_run.get_runs_by_project_id(db, project_id=project_id, page=page, page_size=page_size)
    total_pages = math.ceil(total_runs / page_size)

    logger.info(f"Project detail page accessed for project ID: {project_id}. Page: {page}/{total_pages}")
    return templates.TemplateResponse("project_detail.html", {
        "request": request,
        "project": project,
        "schedules": schedules_data,
        "runs": runs_data,
        "current_page": page,
        "total_pages": total_pages,
        "page_size": page_size
    })

@app.post("/projects/{project_id}/run", response_class=RedirectResponse)
async def run_project_now(project_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run_create = schema_run.RunCreate(project_id=project_id, schedule_id=None) # Explicitly set schedule_id to None
    db_run = crud_run.create_run(db=db, run=run_create)
    background_tasks.add_task(execute_script, db, db_run.id)
    logger.info(f"Manually triggered run for project ID {project_id}. Run ID: {db_run.id}")
    return RedirectResponse(url=f"/runs/{db_run.id}", status_code=303)

@app.post("/projects/{project_id}/run-scheduled/{schedule_id}", response_class=RedirectResponse)
async def run_scheduled_job(
    project_id: int,
    schedule_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    run_create = schema_run.RunCreate(project_id=project_id, schedule_id=schedule_id)
    db_run = crud_run.create_run(db=db, run=run_create)
    background_tasks.add_task(execute_script, db, db_run.id)
    logger.info(f"Scheduled job triggered for project ID {project_id}, schedule ID {schedule_id}. Run ID: {db_run.id}")
    return RedirectResponse(url=f"/runs/{db_run.id}", status_code=303)

@app.get("/schedules/{schedule_id}", response_class=HTMLResponse)
async def schedule_detail(request: Request, schedule_id: int, db: Session = Depends(get_db)):
    schedule = crud_schedule.get_schedule(db, schedule_id=schedule_id)
    if schedule is None:
        logger.warning(f"Attempted to view details of non-existent schedule with ID: {schedule_id}")
        raise HTTPException(status_code=404, detail="Schedule not found")
    logger.info(f"Schedule detail page accessed for schedule ID: {schedule_id}")
    return templates.TemplateResponse("schedule_detail.html", {"request": request, "schedule": schedule})

@app.get("/runs/{run_id}", response_class=HTMLResponse)
async def run_detail(request: Request, run_id: int, db: Session = Depends(get_db)):
    run = crud_run.get_run(db, run_id=run_id)
    if run is None:
        logger.warning(f"Attempted to view details of non-existent run with ID: {run_id}")
        raise HTTPException(status_code=404, detail="Run not found")
    logger.info(f"Run detail page accessed for run ID: {run_id}")
    return templates.TemplateResponse("run_detail.html", {"request": request, "run": run})

# Include the routers after the add routes
app.include_router(projects.router)
app.include_router(schedules.router)
app.include_router(runs.router)
