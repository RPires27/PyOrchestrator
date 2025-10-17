from fastapi import APIRouter

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)

@router.get("/")
def read_projects():
    return []
