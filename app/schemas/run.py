from pydantic import BaseModel
from datetime import datetime

class RunBase(BaseModel):
    project_id: int
    schedule_id: int | None = None
    status: str = "pending"
    log_output: str | None = None

class RunCreate(RunBase):
    pass

class Run(RunBase):
    id: int
    start_time: datetime
    end_time: datetime | None = None

    class Config:
        from_attributes = True
