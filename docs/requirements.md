# Loan Management App Requirements Document

## 1. Project Title

Internal Loan Management System

## 2. Purpose

This application will help a small lender manage the full lifecycle of loans issued to borrowers. The system will be used primarily as an internal tool to record borrowers, issue loans, track repayments, monitor balances, identify overdue accounts, and maintain a reliable financial history.

The project also serves as a software engineering exercise, so the system should be designed with clear requirements, clean architecture, maintainability, correctness, and testability in mind.

## 3. Problem Statement

Managing loans manually through notebooks, spreadsheets, or chat messages can lead to errors, missing records, unclear balances, and difficulty tracking overdue borrowers. The lender needs a secure and structured system that provides an accurate record of:

* who borrowed money
* how much was borrowed
* when repayment is due
* what has already been paid
* what remains outstanding
* which loans are overdue

## 4. Goals

The main goals of the system are:

1. Record and organize borrower information.
2. Create and manage loan records.
3. Generate repayment schedules based on defined loan terms.
4. Record repayments and update balances accurately.
5. Detect and display overdue loans and missed installments.
6. Maintain a transparent history of all loan-related activity.
7. Provide a foundation for future expansion such as reminders, borrower portals, and analytics.

## 5. Primary Users

### 5.1 Admin / Lender

The main user of the system. This user can:

* create and edit borrower profiles
* create and manage loans
* record payments
* view reports and overdue accounts
* manage application settings

### 5.2 Staff User (Future)

A secondary internal user who may be allowed to record payments and view loan records, depending on permissions.

### 5.3 Borrower (Out of Scope for V1)

In future versions, borrowers may log in to see their loan status, repayment history, and upcoming due dates.

## 6. Scope

### 6.1 In Scope for Version 1

The first version of the system will include:

* user login for internal users
* borrower profile management
* loan creation and tracking
* repayment schedule generation
* payment recording
* balance calculation
* overdue loan detection
* borrower loan history
* active and closed loan views
* basic reports/dashboard
* audit trail for important changes

### 6.2 Out of Scope for Version 1

The following are intentionally excluded from the first version:

* mobile app
* borrower self-service portal
* automatic SMS, WhatsApp, or email reminders
* integration with payment providers or mobile money
* credit scoring or AI-based loan approval
* public loan application workflows
* multi-branch operations
* advanced accounting integrations

## 7. Business Context and Assumptions

This system is intended as an internal loan tracking and management platform for a small lender. It is not initially intended to serve as a public fintech platform.

Version 1 assumes:

* the lender enters borrower and loan data manually
* repayments are manually recorded by the lender or staff
* loan terms are agreed outside the system and then entered into it
* legal agreements and compliance processes may exist outside the system initially

## 8. Functional Requirements

### 8.1 User Authentication and Access

The system shall:

* allow internal users to log in securely
* restrict access to authenticated users only
* support user roles such as admin and staff
* prevent unauthorized users from viewing loan data

### 8.2 Borrower Management

The system shall allow the user to:

* create a borrower profile
* view a list of all borrowers
* search for a borrower by name, phone number, or ID
* view a borrower’s details
* edit borrower information
* mark a borrower as active or inactive

A borrower profile should include:

* full name
* phone number
* national ID / passport / other identifier
* address
* notes
* date created
* status

### 8.3 Loan Management

The system shall allow the user to:

* create a loan for a borrower
* assign loan terms and conditions
* view all loans
* filter loans by status
* view detailed information for a specific loan
* mark loans as active, closed, overdue, defaulted, or restructured

Each loan shall store:

* borrower
* principal amount
* interest rate
* interest calculation type
* repayment frequency
* term length
* start date
* due date
* status
* notes
* created by
* date created

### 8.4 Repayment Schedule Generation

The system shall:

* generate a repayment schedule when a loan is created
* compute installment amounts according to defined loan rules
* store due dates and due amounts for each installment
* support at least weekly and monthly repayment frequencies in V1

Each repayment schedule item should include:

* installment number
* due date
* principal due
* interest due
* penalty due
* total due
* paid amount
* remaining amount
* status

### 8.5 Payment Recording

The system shall allow the user to:

* record a borrower payment against a loan
* specify payment amount, date, method, and reference
* support partial payments
* support full repayment
* attach notes to the payment

The system shall:

* update loan balance after each payment
* allocate payments according to a defined policy
* prevent invalid payment entries
* preserve payment history

### 8.6 Balance and Outstanding Amount Calculation

The system shall:

* calculate outstanding principal
* calculate outstanding interest
* calculate overdue amount
* calculate total remaining balance
* show how much is due next and when

### 8.7 Overdue and Arrears Tracking

The system shall:

* identify missed installments
* flag loans with overdue payments
* display the number of days overdue
* show overdue totals on the dashboard and loan detail pages

### 8.8 Loan History and Audit Trail

The system shall maintain a historical record of:

* loan creation
* payment entries
* loan status changes
* edits to important records

The audit trail should capture:

* who made the change
* when the change was made
* what was changed

### 8.9 Dashboard and Reporting

The system shall provide a dashboard showing:

* number of active loans
* number of closed loans
* total outstanding balance
* overdue loans
* repayments recorded recently

The system should also provide reports or views for:

* all borrowers
* active loans
* overdue loans
* loans nearing due date
* payment history by borrower

## 9. Business Rules

These are initial business rules for Version 1 and may be refined later.

1. A borrower may have one or more loans.
2. Every loan must belong to exactly one borrower.
3. Every payment must belong to exactly one loan.
4. A loan cannot exist without a principal amount greater than zero.
5. A payment amount must be greater than zero.
6. A loan start date must be on or before its due date.
7. Each loan must have a defined repayment frequency.
8. Payments must not be deleted silently; important changes should be auditable.
9. Loan balances must be derived consistently from the loan schedule and payment records.
10. The system must not use floating-point arithmetic for money.

### 9.1 Business Rules Requiring Final Decision

The following require a concrete policy before implementation:

* whether interest is flat-rate or reducing-balance
* whether borrowers can hold multiple active loans simultaneously
* how late penalties are calculated
* how payments are allocated (penalty first, interest first, or principal first)
* whether early repayment changes interest owed
* whether overpayment is allowed and how it is handled
* whether loan restructuring is supported in V1 or only later

## 10. Non-Functional Requirements

### 10.1 Accuracy

The system must calculate balances and repayment amounts accurately.
Money values must use decimal-safe or integer-based representations.

### 10.2 Security

The system must:

* require authentication
* protect sensitive borrower data
* store passwords securely using hashing
* restrict actions based on user roles
* protect against common web vulnerabilities

### 10.3 Reliability

The system should preserve data integrity and avoid inconsistent loan states.
Important records should not be lost because of simple user mistakes.

### 10.4 Maintainability

The codebase should be modular and organized so that business logic, database logic, and user interface logic are clearly separated.

### 10.5 Testability

The system should be designed so that financial calculations and business rules can be tested independently.

### 10.6 Performance

For V1, the system should perform well for a small-to-medium internal dataset, such as hundreds or thousands of borrowers and loans.

### 10.7 Auditability

Important loan and payment actions should be traceable through logs or audit records.

## 11. Data Requirements

The system will manage the following main types of data:

* user accounts
* borrower profiles
* loan records
* repayment schedule items
* payment records
* penalties (if implemented)
* audit log entries

## 12. Constraints

* The system is initially intended for internal use only.
* The first version should remain simple enough for a single developer to build and maintain.
* The system should be implementable with a modern web stack and a relational database.
* Legal compliance workflows are not fully automated in V1.

## 13. Risks

Potential risks include:

* unclear business rules around interest and penalties
* incorrect financial calculations
* inconsistent payment allocation logic
* scope creep from adding advanced fintech features too early
* weak audit trail leading to disputes about balances

## 14. Success Criteria

Version 1 will be considered successful if the system allows the lender to:

* create and manage borrowers
* issue loans with clear terms
* generate and store repayment schedules
* record payments accurately
* view up-to-date balances
* identify overdue borrowers quickly
* review the full payment and loan history for each borrower

## 15. Future Enhancements

Possible future enhancements include:

* SMS / WhatsApp reminders
* borrower login portal
* document uploads and scanned agreements
* mobile app access
* payment provider integration
* analytics and forecasting
* multi-currency support
* guarantor and collateral management
* PDF statement generation
* automated delinquency workflows

## 16. Open Questions

These questions should be resolved before detailed implementation begins:

1. What exact interest model will be used?
2. What repayment frequencies must be supported in V1?
3. What is the policy for missed payments?
4. What is the policy for partial payments?
5. Are penalties required in V1?
6. Can a borrower have multiple simultaneous active loans?
7. What statuses should be officially supported for loans and schedule items?
8. Should documents such as signed agreements be stored in V1?
9. What reports are most important to the lender day-to-day?
10. What fields are mandatory for borrower identity verification?

## 17. Recommended Next Deliverables

After approving this requirements document, the next project artifacts should be:

1. business rules specification
2. entity-relationship diagram (ERD)
3. API specification
4. user stories
5. database schema
6. milestone implementation plan

---

This document is intended to serve as the initial requirements baseline for the Internal Loan Management System and can be refined as business rules become more precise.
