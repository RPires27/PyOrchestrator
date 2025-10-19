import subprocess
from sqlalchemy.orm import Session
from app.crud import run as crud_run
from app.models.project import Project
import os
import git # Import GitPython
from app.core.logging_config import setup_logging # Import setup_logging

logger = setup_logging()

def sync_project_dependencies(project_path: str, environment_type: str):
    logger.info(f"Syncing dependencies for project at {project_path} using {environment_type}")
    if environment_type == "uv":
        logger.info(f"Running uv sync in {project_path}")
        subprocess.run(["uv", "sync"], cwd=project_path, check=True)
    elif environment_type == "venv":
        venv_path = os.path.join(project_path, ".venv")
        if not os.path.isdir(venv_path):
            logger.info(f"Creating venv at {venv_path}")
            subprocess.run(["python", "-m", "venv", venv_path], cwd=project_path, check=True)
        
        pip_executable = os.path.join(venv_path, "bin", "pip")
        logger.info(f"Installing requirements in venv at {venv_path}")
        subprocess.run([pip_executable, "install", "-r", "requirements.txt"], cwd=project_path, check=True)
    else:
        raise ValueError(f"Unsupported environment type: {environment_type}")

def execute_script(db: Session, run_id: int):
    db_run = crud_run.get_run(db, run_id)
    if not db_run:
        logger.warning(f"Run ID {run_id} not found for execution.")
        return

    logger.info(f"Starting execution for Run ID: {run_id}, Project ID: {db_run.project_id}")
    crud_run.update_run_status(db, run_id, "running")

    project = db.query(Project).filter(Project.id == db_run.project_id).first()
    if not project:
        error_msg = f"Project not found for Run ID {run_id}."
        logger.error(error_msg)
        crud_run.update_run_status(db, run_id, "failed", error_msg)
        return

    try:
        project_path = project.source_path
        log_message = ""

        if project.source_type == "GitHub":
            if not project.source_url:
                error_msg = "GitHub project requires a source_url."
                logger.error(error_msg)
                crud_run.update_run_status(db, run_id, "failed", error_msg)
                return

            repo_name = project.source_url.split("/")[-1].replace(".git", "")
            destination_path = os.path.join(project.source_path, repo_name)
            logger.info(f"Handling GitHub project: {project.name}. Destination: {destination_path}")

            # If the directory exists and is a git repo, pull.
            if os.path.isdir(os.path.join(destination_path, '.git')):
                logger.info(f"Pulling updates for repository at {destination_path}")
                repo = git.Repo(destination_path)
                origin = repo.remotes.origin
                origin.pull()
                log_message += f"Pulled updates for repository at {destination_path}\n"
            # If the directory exists but is not a git repo, or doesn't exist, clone.
            else:
                if not os.path.exists(destination_path):
                    os.makedirs(destination_path)
                    logger.info(f"Created directory: {destination_path}")
                logger.info(f"Cloning repository from {project.source_url} to {destination_path}")
                git.Repo.clone_from(project.source_url, destination_path)
                log_message += f"Cloned repository from {project.source_url} to {destination_path}\n"
            
            project_path = destination_path # Use the new destination_path for the rest of the script

        elif project.source_type == "Local":
            logger.info(f"Using local project at {project_path}")
            log_message += f"Using local project at {project_path}\n"
        else:
            error_msg = f"Unsupported source type: {project.source_type}"
            logger.error(error_msg)
            crud_run.update_run_status(db, run_id, "failed", error_msg)
            return

        if not os.path.isdir(project_path):
            error_msg = f"Project path not found: {project_path}"
            logger.error(error_msg)
            crud_run.update_run_status(db, run_id, "failed", error_msg)
            return

        sync_project_dependencies(project_path, project.environment_type)

        if project.environment_type == "uv":
            command = ["uv", "run", project.main_script]
        elif project.environment_type == "venv":
            venv_path = os.path.join(project_path, ".venv")
            python_executable = os.path.join(venv_path, "bin", "python")
            command = [python_executable, project.main_script]
        else:
            # This case is already handled in sync_project_dependencies, but as a safeguard:
            error_msg = f"Unsupported environment type: {project.environment_type}"
            logger.error(error_msg)
            crud_run.update_run_status(db, run_id, "failed", error_msg)
            return

        if project.arguments:
            command.extend(project.arguments.split())
            logger.info(f"Executing command with arguments: {' '.join(command)}")
        else:
            logger.info(f"Executing command: {' '.join(command)}")

        result = subprocess.run(command, cwd=project_path, capture_output=True, text=True)
        log_message += f"Script stdout:\n{result.stdout}\nScript stderr:\n{result.stderr}"

        if result.returncode == 0:
            logger.info(f"Run ID {run_id} completed successfully.")
            crud_run.update_run_status(db, run_id, "completed", log_message)
        else:
            logger.error(f"Run ID {run_id} failed with exit code {result.returncode}.")
            crud_run.update_run_status(db, run_id, "failed", log_message)

    except subprocess.CalledProcessError as e:
        error_msg = f"Subprocess failed for Run ID {run_id}: {e.stderr}"
        logger.error(error_msg)
        crud_run.update_run_status(db, run_id, "failed", log_message + "\n" + error_msg)
    except git.InvalidGitRepositoryError as e:
        error_msg = f"Invalid Git repository for Run ID {run_id}: {e}"
        logger.error(error_msg)
        crud_run.update_run_status(db, run_id, "failed", log_message + "\n" + error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during execution for Run ID {run_id}: {e}"
        logger.getLogger().exception(error_msg) # Use exception for full traceback
        crud_run.update_run_status(db, run_id, "failed", log_message + "\n" + error_msg)