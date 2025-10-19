from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    cron_schedule = Column(String)
    timezone = Column(String, default="UTC")
    schedule_type = Column(String, default="cron") # cron or simple
    run_days = Column(String, nullable=True) # Comma-separated days, e.g., "MON,TUE,WED"
    run_time = Column(String, nullable=True) # HH:MM format, e.g., "10:00"
    
    project = relationship("Project", back_populates="schedules")
    runs = relationship("Run", back_populates="schedule", cascade="all, delete-orphan")