import subprocess
from sqlalchemy.orm import Session
from app.crud import run as crud_run
from app.models.project import Project
import os

def execute_script(db: Session, run_id: int):
    db_run = crud_run.get_run(db, run_id)
    if not db_run:
        return

    crud_run.update_run_status(db, run_id, "running")

    project = db.query(Project).filter(Project.id == db_run.project_id).first()
    if not project:
        crud_run.update_run_status(db, run_id, "failed", "Project not found.")
        return

    try:
        if project.source_type == "Local":
            project_path = project.source_path
        else:
            # For now, we only support Local projects
            crud_run.update_run_status(db, run_id, "failed", "GitHub projects are not yet supported.")
            return

        if not os.path.isdir(project_path):
            crud_run.update_run_status(db, run_id, "failed", f"Project path not found: {project_path}")
            return

        if project.environment_type == "uv":
            # Ensure uv is installed and in the PATH
            # For simplicity, we'll assume it is for now.
            subprocess.run(["uv", "sync"], cwd=project_path, check=True)
            command = ["uv", "run", project.main_script]
        elif project.environment_type == "venv":
            venv_path = os.path.join(project_path, ".venv")
            if not os.path.isdir(venv_path):
                subprocess.run(["python", "-m", "venv", venv_path], cwd=project_path, check=True)
            
            pip_executable = os.path.join(venv_path, "bin", "pip")
            python_executable = os.path.join(venv_path, "bin", "python")

            subprocess.run([pip_executable, "install", "-r", "requirements.txt"], cwd=project_path, check=True)
            command = [python_executable, project.main_script]
        else:
            crud_run.update_run_status(db, run_id, "failed", f"Unsupported environment type: {project.environment_type}")
            return

        if project.arguments:
            command.extend(project.arguments.split())

        result = subprocess.run(command, cwd=project_path, capture_output=True, text=True)

        if result.returncode == 0:
            crud_run.update_run_status(db, run_id, "completed", result.stdout)
        else:
            crud_run.update_run_status(db, run_id, "failed", result.stderr)

    except Exception as e:
        crud_run.update_run_status(db, run_id, "failed", str(e))