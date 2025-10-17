from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base

class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="pending") # pending, running, completed, failed
    log_output = Column(String, nullable=True)

    project = relationship("Project", back_populates="runs")
    schedule = relationship("Schedule", back_populates="runs")