import subprocess
from sqlalchemy.orm import Session
from app.crud import run as crud_run
from app.models.project import Project
import os
import git # Import GitPython

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
        project_path = project.source_path
        log_message = ""

        if project.source_type == "GitHub":
            if not project.source_url:
                crud_run.update_run_status(db, run_id, "failed", "GitHub project requires a source_url.")
                return

            repo_name = project.source_url.split("/")[-1].replace(".git", "")
            destination_path = os.path.join(project.source_path, repo_name)

            # If the directory exists and is a git repo, pull.
            if os.path.isdir(os.path.join(destination_path, '.git')):
                repo = git.Repo(destination_path)
                origin = repo.remotes.origin
                origin.pull()
                log_message += f"Pulled updates for repository at {destination_path}\n"
            # If the directory exists but is not a git repo, or doesn't exist, clone.
            else:
                git.Repo.clone_from(project.source_url, destination_path)
                log_message += f"Cloned repository from {project.source_url} to {destination_path}\n"
            
            project_path = destination_path # Use the new destination_path for the rest of the script

        elif project.source_type == "Local":
            log_message += f"Using local project at {project_path}\n"
        else:
            crud_run.update_run_status(db, run_id, "failed", f"Unsupported source type: {project.source_type}")
            return

        if not os.path.isdir(project_path):
            crud_run.update_run_status(db, run_id, "failed", f"Project path not found: {project_path}")
            return

        # Environment setup and script execution (rest of the existing code)
        if project.environment_type == "uv":
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
        log_message += f"Script stdout:\n{result.stdout}\nScript stderr:\n{result.stderr}"

        if result.returncode == 0:
            crud_run.update_run_status(db, run_id, "completed", log_message)
        else:
            crud_run.update_run_status(db, run_id, "failed", log_message)

    except Exception as e:
        crud_run.update_run_status(db, run_id, "failed", str(e))