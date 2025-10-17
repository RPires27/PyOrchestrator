from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.base import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    source_type = Column(String)
    source_url = Column(String, nullable=True)
    source_path = Column(String, nullable=True)
    main_script = Column(String)
    arguments = Column(String, nullable=True)
    environment_type = Column(String)

    schedules = relationship("Schedule", back_populates="project", cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="project", cascade="all, delete-orphan")