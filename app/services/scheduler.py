from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.crud import run as crud_run
from app.schemas import run as schema_run
import httpx
import os
from dotenv import load_dotenv
from app.core.logging_config import setup_logging # Import setup_logging

logger = setup_logging()
load_dotenv() # Load environment variables from .env file

FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")

class SchedulerService:
    def __init__(self, db: Session):
        self.scheduler = BackgroundScheduler()
        self.db = db

    def schedule_job(self, schedule_id: int, project_id: int, cron_schedule: str):
        try:
            self.scheduler.add_job(
                self.run_job,
                CronTrigger.from_crontab(cron_schedule),
                id=str(schedule_id),
                args=[project_id, schedule_id],
            )
            logger.info(f"Scheduled job ID {schedule_id} for project {project_id} with cron: {cron_schedule}")
        except Exception as e:
            logger.error(f"Error scheduling job ID {schedule_id} for project {project_id} with cron {cron_schedule}: {e}")

    def remove_job(self, schedule_id: int):
        try:
            self.scheduler.remove_job(str(schedule_id))
            logger.info(f"Removed job ID {schedule_id} from scheduler.")
        except Exception as e:
            logger.error(f"Error removing job ID {schedule_id} from scheduler: {e}")

    def run_job(self, project_id: int, schedule_id: int):
        logger.info(f"Scheduler triggering run for project {project_id}, schedule {schedule_id}.")
        try:
            with httpx.Client() as client:
                response = client.post(f"{FASTAPI_BASE_URL}/projects/{project_id}/run")
                response.raise_for_status() # Raise an exception for bad status codes
            logger.info(f"Successfully triggered run for project {project_id}, schedule {schedule_id} via API. Response: {response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"HTTPX Request Error when triggering run for project {project_id}, schedule {schedule_id}: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Status Error when triggering run for project {project_id}, schedule {schedule_id}: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Unexpected error when triggering run for project {project_id}, schedule {schedule_id}: {e}")

    def start(self):
        self.scheduler.start()
        logger.info("Scheduler started.")

    def shutdown(self):
        self.scheduler.shutdown()
        logger.info("Scheduler shutdown.")