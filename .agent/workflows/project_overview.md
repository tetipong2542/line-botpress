---
description: Project overview and context for AI coding agents working on the Flask-based Personal Finance app with LINE/Botpress integration
---

## Quick context for AI coding agents

This repository is a Flask-based Personal Finance Management application (Income/Expenses) with LINE integration and Botpress support. It is designed for deploying on Railway.

- **Entry point**: `run.py` — imports `create_app` from `app/__init__.py`. It initializes the Flask app and runs `initialize_database()` on first startup if needed.
- **DB models**: Located in `app/models/`. Key models: `Transaction`, `User`, `Project`, `Category`, `Budget`, `Loan`, `SavingsGoal`. 
- **Services**: Business logic lives in `app/services/`. Key services: `TransactionService` (CRUD, validation), `BotpressService` (webhook handling), `AiAnalyticsService`.
- **Configuration**: `app/config.py` handles environment variables and directory selection for SQLite (`/data` on Railway vs `instance/` locally).

## Important patterns & rules (copy/paste friendly)

- **Database**: 
    - Uses **SQLite** by default.
    - **Migrations**: Uses `Flask-Migrate`. `app/__init__.py` also contains `run_auto_migrations()` which runs specific `ALTER TABLE` commands on startup to add new columns without full Alembic migrations (useful for SQLite limitations).
    - **Initialization**: `run.py` calls `initialize_database()` which does `db.create_all()`.

- **Transactions & Amounts**:
    - **Currency**: Stored as **Satang** (Integer) in the database (`amount` column).
    - **Conversion**: Logic in `TransactionService` attempts to convert amounts < 1,000,000 from Baht to Satang automatically.
    - **Validation**: Use `TransactionService.create_transaction()` for all creations to ensure permission checks (`_check_project_access`) and data validation.

- **Dates & Times**:
    - **Storage**: Naive UTC datetime in database.
    - **Parsing**: Service layer strips timezone info before saving.
    - **Display**: Backend logic often expects/returns ISO format strings.

- **Authentication**:
    - Primary auth via **LINE Login** (`app/routes/auth.py`).
    - Users are identified by `line_user_id`.
    - `Project` ownership and `ProjectMember` tables control access to data.

## Running & developer workflows (Mac/Linux)

- **Prerequisites**: Python 3.9+, `.env` file (copy from `.env.example`).
- **Quick start**:
    1. Create venv: `python3 -m venv venv` && `source venv/bin/activate`
    2. Install deps: `pip install -r requirements.txt`
    3. Run: `python run.py` (App starts on port 5000)
- **Database File**:
    - Locally: usually created in `instance/finance.db` or `app/finance.db` depending on `DATA_DIR` config.
    - **Caution**: Back up `finance.db` before destructive operations.

## Quick guide for AI coding agents (repo-specific)

This is a Flask app for income/expense tracking with LINE integration.

- **Structure**:
    - `app/__init__.py`: App factory, extensions (DB, Migrate), auto-migration logic.
    - `app/models/`: SQLAlchemy models. `Transaction` handles income/expenses.
    - `app/services/`: **ALL** business logic should go here. Do not put complex logic in routes.
    - `app/routes/`: Flask blueprints (`auth`, `api`, `bot`, `web`, `line`).
    - `app/templates/`: Jinja2 templates for the Web UI.

**Critical patterns and conventions**:
- **Service Layer Pattern**: Always use `TransactionService`, `BudgetService` etc. for DB operations. Do not query models directly in routes unless simple GETs.
- **Permissions**: Services must check `_check_project_access(project_id, user_id)` before modifying data.
- **Auto-Migrations**: If adding a simple column, check `run_auto_migrations` in `app/__init__.py` for the pattern to add it safely on startup.
- **Botpress Integration**: The app acts as a backend for a Botpress bot; logic for this is in `app/routes/bot.py` and `app/services/botpress_service.py`.

**Integration points**:
- **LINE**: `app/routes/line.py` handles LINE messaging API webhooks.
- **Botpress**: `app/routes/bot.py` accepts webhooks from Botpress.

**Troubleshooting & tips**:
- If `TransactionService` errors on amount, check if you are passing Baht (float) or Satang (int).
- If database changes aren't reflecting, check `instance/` folder permissions or `DATA_DIR` env var.
- `app/utils/validators.py` contains shared validation logic.

**Files to inspect quickly**:
- `run.py`: Entry.
- `app/models/transaction.py`: Core data structure.
- `app/services/transaction_service.py`: Core logic.
- `app/config.py`: Deployment paths.
