# Loan Manager

Loan Manager is an internal loan management system for borrowers, loans,
repayment schedules, payments, late charges, reports, and audit history.

The backend uses FastAPI, SQLAlchemy ORM, Alembic, PostgreSQL, and Pydantic.
The frontend uses Next.js, React, TypeScript, and a small internal-tool UI shell.

## Repository Structure

```text
loan-manager/
├── backend/   # FastAPI backend, SQLAlchemy models, Alembic migrations, tests
├── docs/      # Product rules, requirements, ERD, and schema notes
├── frontend/  # Next.js frontend application
└── infra/     # Infrastructure notes
```

## Core Business Rules

- One active loan per borrower in Version 1.
- Monthly periodic interest is 30%; weekly periodic interest is 8%.
- Grace period is 7 days.
- Late charge is a one-time 10% of the unpaid installment amount after grace.
- Payment allocation order is late-charge interest, late-charge principal,
  regular interest, then regular principal.
- Overpayments are rejected.
- Money is handled with `Decimal` and database `NUMERIC`, not floats.

## Getting Started

From the backend directory:

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

Set `DATABASE_URL` and `AUTH_SECRET_KEY` in `.env`, then run migrations:

```bash
alembic upgrade head
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Run backend tests:

```bash
python3 -m unittest discover -s tests/unit -v
```

From the frontend directory:

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

Run frontend checks:

```bash
npm run lint
npm run typecheck
npm run build
```

## Documentation

- Requirements: [`docs/requirements.md`](/home/cmalili/loan-manager/docs/requirements.md)
- Business rules: [`docs/business-rules.md`](/home/cmalili/loan-manager/docs/business-rules.md)
- Database schema: [`docs/database-schema.md`](/home/cmalili/loan-manager/docs/database-schema.md)
- Implementation plan: [`docs/implementation-plan.md`](/home/cmalili/loan-manager/docs/implementation-plan.md)
