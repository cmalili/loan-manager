# Current Tasks

This file tracks the current actionable tasks for the Loan Manager project.

## Current Focus
Refine the first frontend screens, then use visual concepts for the main UI direction.

## Immediate Tasks
- [x] Implement user authentication
- [x] Add password hashing and verification
- [x] Restrict endpoints by role
- [x] Limit correction/reversal actions to admin users
- [x] Test auth and permissions flows

## Near-Term Tasks
- [x] Frontend Phase 9A: set up application structure, routing, auth state, and API client
- [ ] Generate visual concepts for the core internal tool screens
- [ ] Frontend Phase 9B: complete borrower detail/edit/deactivation flows
- [ ] Frontend Phase 9C: build loan detail and repayment schedule views
- [ ] Frontend Phase 9D: browser-test payment entry and recent payment views
- [ ] Frontend Phase 9E: browser-test overdue and dashboard reporting views
- [ ] Frontend Phase 9F: integration polish, protected routes, and UI flow testing

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
- Phase 8 authentication and authorization is now implemented and tested.
- Phase 9A frontend foundation is implemented.
- The next major goal is visual concept work for the core screens before UI polish.
