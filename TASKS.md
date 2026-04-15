# Current Tasks

This file tracks the current actionable tasks for the Loan Manager project.

## Current Focus
Move from overdue logic and late charges into audit logging and reporting.

## Immediate Tasks
- [x] Implement overdue detection
- [x] Apply one-week grace period
- [x] Create one-time 10% late charge for overdue installment
- [x] Link late charge to schedule item
- [x] Implement late-charge interest accrual
- [x] Test overdue and late-charge workflows

## Near-Term Tasks
- [ ] Record audit logs for important actions
- [ ] Add borrower loan history queries
- [ ] Add overdue loans query/view
- [ ] Add recent payments query/view
- [ ] Add dashboard summary queries

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
- Phase 4 repayment schedule generation is now implemented and tested.
- Phase 5 payment recording and allocation is now implemented and tested.
- Phase 6 overdue logic and late charges is now implemented and tested.
- The next major goal is Phase 7 audit and reporting.
