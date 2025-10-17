from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database.base import engine, Base, SessionLocal
from app.routes import projects, schedules, runs
from app.services.scheduler import SchedulerService
from app.crud import schedule as crud_schedule

Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

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

app.include_router(projects.router)
app.include_router(schedules.router)
app.include_router(runs.router)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": "Welcome to the PyOrchestrator"})