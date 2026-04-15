# Current Tasks

This file tracks the current actionable tasks for the Loan Manager project.

## Current Focus
Move from payment recording into overdue logic and late charges.

## Immediate Tasks
- [x] Create payment Pydantic schemas
- [x] Create payment service layer
- [x] Implement payment recording endpoint
- [x] Implement payment allocation logic
- [x] Update schedule item paid fields correctly
- [x] Reject overpayments
- [x] Test partial and full payment flows

## Near-Term Tasks
- [ ] Implement overdue detection
- [ ] Apply one-week grace period
- [ ] Create one-time 10% late charge for overdue installment
- [ ] Link late charge to schedule item
- [ ] Implement late-charge interest accrual

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
- The next major goal is Phase 6 overdue logic and late charges.
