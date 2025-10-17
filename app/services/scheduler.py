from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.crud import run as crud_run
from app.schemas import run as schema_run
from app.services.executor import execute_script

class SchedulerService:
    def __init__(self, db: Session):
        self.scheduler = BackgroundScheduler()
        self.db = db

    def schedule_job(self, schedule_id: int, project_id: int, cron_schedule: str):
        self.scheduler.add_job(
            self.run_job,
            CronTrigger.from_crontab(cron_schedule),
            id=str(schedule_id),
            args=[project_id, schedule_id],
        )

    def remove_job(self, schedule_id: int):
        self.scheduler.remove_job(str(schedule_id))

    def run_job(self, project_id: int, schedule_id: int):
        run = schema_run.RunCreate(project_id=project_id, schedule_id=schedule_id)
        db_run = crud_run.create_run(self.db, run)
        execute_script(self.db, db_run.id)

    def start(self):
        self.scheduler.start()

    def shutdown(self):
        self.scheduler.shutdown()
