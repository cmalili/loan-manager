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
- [ ] Create repayment schedule service
- [ ] Support weekly schedules
- [ ] Support monthly schedules
- [ ] Apply 8% weekly rate correctly
- [ ] Apply 30% monthly rate correctly
- [ ] Store generated repayment schedule items
- [ ] Test schedule totals and installment correctness

## Phase 5 — Payment Recording and Allocation
- [ ] Create Pydantic schemas for payments
- [ ] Create payment service layer
- [ ] Implement payment recording
- [ ] Implement payment allocation logic
- [ ] Allocate in order: late-charge interest → late-charge principal → regular interest → regular principal
- [ ] Update schedule item paid fields correctly
- [ ] Reject overpayments
- [ ] Test partial and full payment flows

## Phase 6 — Overdue Logic and Late Charges
- [ ] Implement overdue detection
- [ ] Apply one-week grace period
- [ ] Create one-time 10% late charge for overdue installment
- [ ] Link late charge to schedule item
- [ ] Implement late-charge interest accrual
- [ ] Track waived amounts separately
- [ ] Test overdue and late-charge workflows

## Phase 7 — Audit and Reporting
- [ ] Record audit logs for important actions
- [ ] Add borrower loan history queries
- [ ] Add overdue loans query/view
- [ ] Add recent payments query/view
- [ ] Add dashboard summary queries
- [ ] Test reporting consistency against source data

## Phase 8 — Authentication and Authorization
- [ ] Implement user authentication
- [ ] Add password hashing and verification
- [ ] Restrict endpoints by role
- [ ] Limit correction/reversal actions to admin users
- [ ] Test auth and permissions flows

## Phase 9 — Frontend
- [ ] Set up frontend application structure
- [ ] Build borrower pages
- [ ] Build loan pages
- [ ] Build payment entry page
- [ ] Build overdue loans page
- [ ] Connect frontend to backend API
- [ ] Test basic end-to-end UI flows

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
