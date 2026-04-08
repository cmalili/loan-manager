# Current Tasks

This file tracks the current actionable tasks for the Loan Manager project.

## Current Focus
Build the first backend vertical slice: borrower management.

## Immediate Tasks
- [ ] Review current backend structure after migration setup
- [ ] Confirm `backend/app/db/session.py` exists and is correctly configured
- [ ] Create Pydantic borrower schemas
- [ ] Create borrower service layer
- [ ] Create borrower API routes
- [ ] Wire borrower routes into the FastAPI app
- [ ] Test borrower CRUD end to end

## Near-Term Tasks
- [ ] Create loan Pydantic schemas
- [ ] Create loan service layer
- [ ] Implement create loan endpoint
- [ ] Implement repayment schedule generation service

## Project Hygiene
- [ ] Commit current database milestone
- [ ] Push current progress to GitHub
- [ ] Add PostgreSQL and Alembic setup notes to README
- [ ] Add required backend dependencies to a project dependency file

## Notes
- The PostgreSQL database is running locally.
- The initial Alembic migration has been applied successfully.
- The database tables now exist.
- The next major goal is to move from database setup into actual API functionality.
