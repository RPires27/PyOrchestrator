# PyOrchestrator

A lightweight Python Orchestrator Web Tool designed to streamline and automate the scheduling and execution of Python scripts. It provides a web-based dashboard to manage automation projects, schedule their runs, and view execution logs, offering a flexible and code-centric alternative to traditional automation platforms.

## ✨ Features

### Core Functionality

- **Project Management:** Add, manage, edit, and delete automation projects with details like name, source type (GitHub/Local), script path, arguments, and environment type (uv/venv).
- **Flexible Scheduling:**
    - **Simple Mode:** Schedule jobs by selecting days of the week and a specific time, no cron knowledge required.
    - **Advanced Mode:** Use standard cron expressions for complex scheduling needs.
- **Timezone Support:** Each schedule can have its own timezone to ensure jobs run at the correct local time.
- **Manual Triggers:** Manually trigger project or schedule runs directly from the web UI.
- **Environment Handling:** Supports both `uv` and `venv` for isolated and efficient dependency management. `uv` automatically handles `pyproject.toml` and `requirements.txt`.
- **Dependency Management:** Manually re-sync project dependencies from the UI.
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
- **Timezones:** pytz
- **Environment Variables:** python-dotenv

## 📦 Setup and Installation

### Prerequisites

- Python 3.11+ (recommended)
- `uv` (install with `pip install uv`) or `pip`

### Local Development Setup

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

## 🖥️ Usage

1.  **Access the Dashboard:** Open your web browser and navigate to `http://localhost:8000`.
2.  **Manage Projects:**
    - Click "Add New Project" to create a new automation project.
    - From the dashboard, click "View Details" on a project to see its schedules and runs.
    - On the project detail page, you can "Edit Project", "Run Project Now", "Re-sync Dependencies", or "Delete Project".
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
│   ├── core/                 # Core utilities (logging, timezones)
│   ├── crud/                 # CRUD operations for database models
│   ├── database/             # Database setup and session management
│   ├── models/               # SQLAlchemy ORM models
│   ├── routes/               # FastAPI API routes
│   ├── schemas/              # Pydantic schemas for data validation
│   ├── services/             # Business logic (scheduler, executor)
│   └── main.py               # Main FastAPI application entry point
├── static/                   # Static assets (custom CSS, JS, images). Contains a `.gitkeep` file to ensure it's tracked by Git.
├── templates/                # Jinja2 HTML templates
├── .env.example              # Example environment variables file
├── .gitignore
├── pyproject.toml
├── uv.lock
├── README.md
└── orchestrator.log          # Application log file
```

## 💡 Future Enhancements

- **User Authentication:** Secure access with user accounts and roles (currently postponed).
- **Notifications:** Implement email/other notifications for failed runs (currently postponed).
- **UI Improvements:** Filtering and search capabilities for tables.
- **Advanced Environment Management:** UI for viewing installed packages or recreating virtual environments.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
