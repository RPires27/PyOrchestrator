from pydantic import BaseModel

class ProjectBase(BaseModel):
    name: str
    source_type: str
    source_url: str | None = None
    source_path: str | None = None
    main_script: str
    arguments: str | None = None
    environment_type: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int

    class Config:
        from_attributes = True
