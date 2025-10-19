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
    
    project = relationship("Project", back_populates="schedules")
    runs = relationship("Run", back_populates="schedule", cascade="all, delete-orphan")
