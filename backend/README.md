# Backend

FastAPI backend for the internal Loan Manager system.

## Structure

- `app/api/` contains route handlers and dependency wiring.
- `app/core/` contains settings and security helpers.
- `app/db/` contains database session setup.
- `app/models/` contains SQLAlchemy ORM models.
- `app/schemas/` contains Pydantic request and response schemas.
- `app/services/` contains business workflows and financial rules.
- `alembic/` contains PostgreSQL migrations.
- `tests/` contains unit tests.

Keep business logic in `app/services/`; route handlers should stay thin.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env before sourcing it.
set -a
source .env
set +a
```

Set `DATABASE_URL` to a PostgreSQL database, then run:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Run tests with:

```bash
python3 -m unittest discover -s tests/unit -v
```
