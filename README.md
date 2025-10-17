# PyOrchestrator

A lightweight Python Orchestrator Web Tool designed to streamline and automate the scheduling and execution of Python scripts. It provides a web-based dashboard to manage automation projects, schedule their runs, and view execution logs, offering a flexible and code-centric alternative to traditional automation platforms.

## ✨ Features

### Core Functionality

- **Project Management:** Add, manage, edit, and delete automation projects with details like name, source type (GitHub/Local), script path, arguments, and environment type (uv/venv).
- **Script Scheduling:** Schedule scripts to run at specified intervals using cron expressions.
- **Manual Triggers:** Manually trigger project or schedule runs directly from the web UI.
- **Environment Handling:** Supports both `uv` and `venv` for isolated and efficient dependency management.
- **Execution Logging:** Stores detailed logs and results for each script run.
- **GitHub Integration:** Automatically clones or pulls updates for projects hosted on GitHub.

### User Interface (UI)

- **Modern Dashboard:** A clean, responsive, and intuitive web interface built with FastAPI and Bootstrap 5.
- **Project-Centric View:** The main dashboard lists projects, with detailed schedules and runs accessible on each project's dedicated detail page.
- **Theme Toggle:** Switch between dark and light modes with a single click, with preference persistence.
- **Pagination:** Efficiently browse through extensive run histories with pagination controls.

### Robustness & Maintainability

- **Advanced Logging:** Structured logging to console and a dedicated `orchestrator.log` file for better monitoring and debugging.
- **Configuration Management:** Utilizes `.env` files for flexible and secure environment variable management.

## 🚀 Technologies Used

- **Backend:** FastAPI (Python)
- **Database:** SQLite (for MVP)
- **ORM:** SQLAlchemy
- **Scheduler:** APScheduler
- **Dependency Management:** uv
- **Git Operations:** GitPython
- **Web Server:** Uvicorn
- **Frontend:** Jinja2 Templates, Bootstrap 5, Bootstrap Icons
- **Environment Variables:** python-dotenv

## 📦 Setup and Installation

### Prerequisites

- Python 3.11+ (recommended)
- `uv` (install with `pip install uv`) or `pip`
- Docker and Docker Compose (for containerized setup)

### 1. Local Development Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/PyOrchestrator.git # Replace with actual repo URL
    cd PyOrchestrator
    ```

2.  **Install dependencies:**

    ```bash
    uv sync
    ```

3.  **Create a `.env` file:**
    Create a file named `.env` in the project root and add your configuration. Example:

    ```env
    DATABASE_URL="sqlite:///./orchestrator.db"
    FASTAPI_BASE_URL="http://localhost:8000"
    ```

4.  **Run the application:**
    ```bash
    uv run uvicorn app.main:app --reload
    ```
    The application will be accessible at `http://localhost:8000`.

### 2. Docker Setup (Recommended)

1.  **Ensure Docker is running** on your system.

2.  **Build the Docker image:**

    ```bash
    docker-compose build
    ```

3.  **Create a `.env` file** (as described in step 3 of Local Development Setup).

4.  **Run the application using Docker Compose:**

    ```bash
    docker-compose up
    ```

    The application will be accessible at `http://localhost:8000`.

5.  **To stop the application:**
    ```bash
    docker-compose down
    ```

## 🖥️ Usage

1.  **Access the Dashboard:** Open your web browser and navigate to `http://localhost:8000`.
2.  **Manage Projects:**
    - Click "Add New Project" to create a new automation project.
    - From the dashboard, click "View Details" on a project to see its schedules and runs.
    - On the project detail page, you can "Edit Project", "Run Project Now", or "Delete Project".
3.  **Manage Schedules:**
    - On a project detail page, click "Add Schedule" to create a new schedule for that project.
    - For existing schedules, you can "Edit", "Delete", or "Run Now" (manually trigger the schedule).
4.  **View Runs:**
    - Access run logs from the "Recent Runs" table on the project detail page.
    - Use the pagination controls to navigate through run history.

## 📂 Project Structure

```
PyOrchestrator/
├── app/
│   ├── core/                 # Core utilities (e.g., logging configuration)
│   ├── crud/                 # CRUD operations for database models
│   ├── database/             # Database setup and session management
│   ├── models/               # SQLAlchemy ORM models
│   ├── routes/               # FastAPI API routes
│   ├── schemas/              # Pydantic schemas for data validation
│   ├── services/             # Business logic (scheduler, executor, notifications)
│   └── main.py               # Main FastAPI application entry point
├── static/                   # Static assets (custom CSS, JS, images)
├── templates/                # Jinja2 HTML templates
├── .env.example              # Example environment variables file
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── README.md
└── orchestrator.log          # Application log file
```

## 💡 Future Enhancements

- **Advanced Environment Management:** Support for `pyproject.toml`, UI for managing virtual environments.
- **Timezone Support:** Allow per-schedule timezone configuration.
- **Notifications:** Implement email/other notifications for failed runs (currently postponed).
- **UI Improvements:** Filtering and search capabilities for tables.
- **User Authentication:** Secure access with user accounts and roles.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. (Note: LICENSE file not yet created)
