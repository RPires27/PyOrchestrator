from pydantic import BaseModel

class ScheduleBase(BaseModel):
    name: str
    project_id: int
    cron_schedule: str
    timezone: str = "UTC"
    schedule_type: str = "cron"
    run_days: str | None = None
    run_time: str | None = None

class ScheduleCreate(ScheduleBase):
    pass

class Schedule(ScheduleBase):
    id: int

    class Config:
        from_attributes = True
