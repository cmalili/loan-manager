# Current Tasks

This file tracks the current actionable tasks for the Loan Manager project.

## Current Focus
Build the first backend vertical slice: borrower management.

## Immediate Tasks
- [x] Review current backend structure after migration setup
- [x] Confirm `backend/app/db/session.py` exists and is correctly configured
- [x] Create Pydantic borrower schemas
- [x] Create borrower service layer
- [x] Create borrower API routes
- [x] Wire borrower routes into the FastAPI app
- [x] Test borrower CRUD end to end

## Near-Term Tasks
- [ ] Create loan Pydantic schemas
- [ ] Create loan service layer
- [ ] Implement create loan endpoint
- [ ] Implement repayment schedule generation service

## Project Hygiene
- [x] Commit current database milestone
- [x] Push current progress to GitHub
- [ ] Add PostgreSQL and Alembic setup notes to README
- [x] Add required backend dependencies to a project dependency file

## Notes
- The PostgreSQL database is running locally.
- The initial Alembic migration has been applied successfully.
- The database tables now exist.
- The borrower vertical slice is now working end to end.
- The next major goal is loan creation and repayment schedule generation.
