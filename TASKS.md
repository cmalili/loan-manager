# Current Tasks

This file tracks the current actionable tasks for the Loan Manager project.

## Current Focus
Move from audit logging and reporting into authentication and authorization.

## Immediate Tasks
- [x] Record audit logs for important actions
- [x] Add borrower loan history queries
- [x] Add overdue loans query/view
- [x] Add recent payments query/view
- [x] Add dashboard summary queries
- [x] Test reporting consistency against source data

## Near-Term Tasks
- [ ] Implement user authentication
- [ ] Add password hashing and verification
- [ ] Restrict endpoints by role
- [ ] Limit correction/reversal actions to admin users
- [ ] Test auth and permissions flows

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
- Phase 7 audit logging and reporting is now implemented and tested.
- The next major goal is Phase 8 authentication and authorization.
