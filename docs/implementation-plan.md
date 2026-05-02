# Loan Manager Implementation Plan
- [x] Test borrower CRUD flow end to end

## Phase 3 — Loan Creation and Validation
- [x] Create Pydantic schemas for loans
- [x] Create loan service layer
- [x] Implement create loan
- [x] Enforce one active loan per borrower
- [x] Enforce loan status rules
- [x] Validate repayment frequency and interest rate rules
- [x] Test loan creation and validation rules

## Phase 4 — Repayment Schedule Generation
- [x] Create repayment schedule service
- [x] Support weekly schedules
- [x] Support monthly schedules
- [x] Apply 8% weekly rate correctly
- [x] Apply 30% monthly rate correctly
- [x] Store generated repayment schedule items
- [x] Test schedule totals and installment correctness

## Phase 5 — Payment Recording and Allocation
- [x] Create Pydantic schemas for payments
- [x] Create payment service layer
- [x] Implement payment recording
- [x] Implement payment allocation logic
- [x] Allocate in order: late-charge interest → late-charge principal → regular interest → regular principal
- [x] Update schedule item paid fields correctly
- [x] Reject overpayments
- [x] Test partial and full payment flows

## Phase 6 — Overdue Logic and Late Charges
- [x] Implement overdue detection
- [x] Apply one-week grace period
- [x] Create one-time 10% late charge for overdue installment
- [x] Link late charge to schedule item
- [x] Implement late-charge interest accrual
- [x] Track waived amounts separately
- [x] Test overdue and late-charge workflows

## Phase 7 — Audit and Reporting
- [x] Record audit logs for important actions
- [x] Add borrower loan history queries
- [x] Add overdue loans query/view
- [x] Add recent payments query/view
- [x] Add dashboard summary queries
- [x] Test reporting consistency against source data

## Phase 8 — Authentication and Authorization
- [x] Implement user authentication
- [x] Add password hashing and verification
- [x] Restrict endpoints by role
- [x] Limit correction/reversal actions to admin users
- [x] Test auth and permissions flows

## Phase 9A — Frontend Foundation
- [x] Set up frontend application structure
- [x] Add routing and app shell
- [x] Implement auth token storage and protected-route handling
- [x] Create API client layer for backend integration
- [x] Test basic authenticated navigation flow

## Phase 9B — Borrower UI
- [x] Build borrower list page
- [ ] Build borrower detail page
- [x] Build borrower create/edit flows
- [ ] Support borrower deactivation flow
- [ ] Test borrower UI flows with a browser

## Phase 9C — Loan UI
- [x] Build loan creation page
- [ ] Build loan detail page
- [ ] Display repayment schedule on loan detail views
- [ ] Test loan creation and loan detail flows with a browser

## Phase 9D — Payment UI
- [x] Build payment entry page
- [x] Show allocation and validation feedback
- [x] Build recent payments view
- [ ] Test payment entry flows with a browser

## Phase 9E — Overdue and Reporting UI
- [x] Build overdue loans page
- [x] Build dashboard summary view
- [x] Surface borrower loan history in the UI
- [ ] Test overdue and reporting flows with a browser

## Phase 9F — Frontend Integration and QA
- [x] Connect all frontend views to backend API
- [x] Validate role-based route protection in the UI
- [ ] Test core end-to-end UI flows
- [ ] Fix integration polish issues across mobile and desktop

## Phase 10 — Quality, Deployment, and Documentation
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Add linting and formatting
- [ ] Add Docker setup
- [ ] Add deployment configuration
- [ ] Add developer setup instructions to README
- [ ] Add API usage examples

## Milestone Rule
A phase should only be marked complete when the related code, tests, and documentation for that phase are in a usable state.
