# Current Tasks

This file tracks the current actionable tasks for the Loan Manager project.

## Current Focus
Move from borrower management into loan creation and repayment schedule generation.

## Immediate Tasks
- [x] Create loan Pydantic schemas
- [x] Create loan service layer
- [x] Implement create loan endpoint
- [ ] Implement repayment schedule generation service
- [ ] Support weekly schedules
- [ ] Support monthly schedules
- [ ] Store generated repayment schedule items
- [ ] Test schedule totals and installment correctness

## Near-Term Tasks
- [ ] Create payment Pydantic schemas
- [ ] Create payment service layer
- [ ] Implement payment recording endpoint
- [ ] Implement payment allocation logic

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
- Phase 3 loan creation and validation is now implemented and wired into the app.
- The next major goal is Phase 4 repayment schedule generation.
