from pydantic import BaseModel

class ScheduleBase(BaseModel):
    name: str
    project_id: int
    cron_schedule: str
    timezone: str = "UTC"

class ScheduleCreate(ScheduleBase):
    pass

class Schedule(ScheduleBase):
    id: int

    class Config:
        from_attributes = True