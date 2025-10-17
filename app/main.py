from fastapi import FastAPI
from app.database.base import engine, Base
from app.routes import projects

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(projects.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the PyOrchestrator"}
