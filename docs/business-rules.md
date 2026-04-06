# Loan Management App Business Rules Document

## 1. Purpose

This document defines the business rules that govern how the Internal Loan Management System behaves. Unlike the requirements document, which describes what the system should do, this document specifies the exact rules the system should follow when managing borrowers, loans, repayment schedules, payments, balances, overdue accounts, and audit history.

These rules are intended to provide a stable basis for the data model, backend logic, API design, validation, and testing strategy.

## 2. Scope

These rules apply to Version 1 of the Internal Loan Management System and are focused on internal loan tracking and management.

## 3. Core Policy for Version 1

To keep Version 1 practical and implementable, the following policy decisions are adopted:

1. The system is for internal staff use only.
2. Borrowers do not log in to the system in Version 1.
3. A borrower may hold more than one loan over time, but only one loan may be marked as **active** at a time in Version 1. This rule is mandatory in Version 1, though it may be relaxed later by configuration or policy change.
4. Interest is calculated using a **periodic interest model**.
5. The periodic interest rate is **30% per month**.
6. Repayment frequencies supported in Version 1 are **weekly** and **monthly**.
7. Partial payments are allowed.
8. Overpayments are not allowed. No rounding tolerance will be accepted in Version 1.
9. Payment allocation will follow the order: **penalty first, then interest, then principal**.
10. Late penalties are modeled as **re-borrowed money** through a structured late-charge mechanism. When an installment remains unpaid beyond the grace period, the system creates a **one-time late charge** linked to that installment. The late charge amount is calculated as a percentage of the unpaid installment amount at the end of the grace period, and interest accrues on that late charge according to the configured periodic interest rules.
11. The grace period for overdue determination is **one week** after the installment due date.
12. Backdated payments are allowed for all admin users.
13. Waived amounts must be tracked separately from paid amounts.
14. Loan history must be auditable. Important financial records should not be silently erased.

## 4. Borrower Rules

### 4.1 Borrower Identity

1. Each borrower must have a unique internal system identifier.
2. A borrower must have a full name.
3. A borrower should have at least one contact field, preferably a phone number.
4. A borrower may have an external identification field such as national ID, passport number, or other identifier.
5. Borrower records may include notes.

### 4.2 Borrower Status

1. A borrower may be marked as **active** or **inactive**.
2. Inactive borrowers remain in the system and retain their history.
3. A borrower with historical loans or payments must not be permanently deleted in ordinary operation.

### 4.3 Borrower and Loans Relationship

1. A borrower may have multiple loans over time.
2. In Version 1, a borrower should not have more than one active loan at the same time unless this rule is deliberately relaxed later.
3. A loan cannot exist without an associated borrower.

## 5. Loan Rules

### 5.1 Loan Creation

1. Every loan must belong to exactly one borrower.
2. Every loan must have a principal amount greater than zero.
3. Every loan must have a start date.
4. Every loan must have a repayment frequency.
5. Every loan must have a term length.
6. Every loan must have an interest rate, even if it is zero.
7. Every loan must have a status.
8. A repayment schedule must be generated when the loan is created.

### 5.2 Loan Statuses

The allowed loan statuses in Version 1 are:

* draft
* active
* closed
* overdue
* defaulted
* restructured
* cancelled

### 5.3 Loan Status Rules

1. A new loan may begin as **draft** until approved or finalized.
2. A loan becomes **active** when it is issued and repayment begins.
3. A loan becomes **overdue** when at least one installment is past due and not fully paid.
4. A loan becomes **closed** when all due amounts are fully paid.
5. A loan may be marked **defaulted** manually if the lender decides it is no longer being repaid under normal expectations.
6. A loan may be marked **restructured** if its terms are formally changed after issuance.
7. A loan marked **cancelled** is treated as never issued for repayment purposes and should not accept payments.

### 5.4 Loan Immutability Rules

1. Once a loan is active, core financial terms should not be edited casually.
2. If major financial terms must change after activation, the change should be handled through a restructuring workflow or audited update.
3. The original loan creation details should remain historically traceable.

## 6. Interest Rules

### 6.1 Interest Model for Version 1

1. Version 1 uses a **periodic interest model**.
2. For monthly repayment schedules, the periodic interest rate is **30% per month**.
3. For weekly repayment schedules, the periodic interest rate is **8% per week**.
4. Interest is not interpreted as a one-time flat contract charge. It is periodic interest that accrues over time.
5. The system must apply the repayment-frequency-specific periodic rate consistently when generating schedules and calculating accruals.
6. The interest formula used in code must be documented and applied consistently across all loans.

### 6.2 Interest Validation

1. Interest rate must not be negative.
2. Zero-interest loans are allowed only if explicitly supported by future policy; Version 1 defaults to the standard periodic interest rule unless deliberately overridden.
3. The system must treat the interest rate as **periodic interest**, not as total contract interest.
4. The system must use one clearly documented interest formula and apply it consistently across all loans.

## 7. Repayment Schedule Rules

### 7.1 Schedule Generation

1. A repayment schedule must be generated automatically when a loan is created.
2. Each installment must have:

   * an installment number
   * a due date
   * principal due
   * interest due
   * penalty due
   * total due
   * paid amount
   * remaining amount
   * status

### 7.2 Supported Frequencies

1. Version 1 supports weekly and monthly schedules.
2. The schedule interval must be derived from the selected repayment frequency.

### 7.3 Schedule Totals

1. The sum of all installment principal amounts must equal the original principal.
2. The sum of all installment interest amounts must equal the total contractual interest.
3. Installment totals must account for rounding in a controlled and documented way.
4. Any rounding difference should be absorbed into the final installment unless another policy is explicitly adopted.

### 7.4 Schedule Item Statuses

Allowed schedule item statuses in Version 1:

* pending
* partially_paid
* paid
* overdue
* waived

### 7.5 Schedule Item Status Rules

1. A schedule item is **pending** when its due date has not passed and it has not been fully paid.
2. A schedule item is **partially_paid** when some amount has been paid but a balance remains.
3. A schedule item is **paid** when the full amount due has been settled.
4. A schedule item is **overdue** when the due date has passed and the amount remains unpaid in full.
5. A schedule item may be **waived** only through an explicit audited action.

## 8. Payment Rules

### 8.1 Payment Creation

1. Every payment must belong to exactly one loan.
2. Every payment must have an amount greater than zero.
3. Every payment must have a payment date.
4. Every payment should record a payment method.
5. Every payment may include a reference value and note.
6. Payments must be recorded in a way that preserves history.

### 8.2 Payment Allocation Policy

Payments in Version 1 must be allocated in the following order:

1. accrued interest on late charges
2. late-charge principal
3. accrued regular interest
4. original principal

Within each category, allocation should be applied to the earliest unpaid obligations first.

### 8.3 Partial Payments

1. Partial payments are allowed.
2. A partial payment reduces the outstanding balance according to the allocation policy.
3. A partially paid installment remains open until fully settled.

### 8.4 Full Payments

1. A payment may settle one installment, multiple installments, or the full remaining loan balance.
2. When all outstanding amounts are settled, the loan status becomes **closed**.

### 8.5 Overpayments

1. In Version 1, the system must reject payments greater than the total outstanding amount.
2. No rounding tolerance is allowed.
3. Excess payments must not be silently accepted.

### 8.6 Backdated Payments

1. Backdated payments are allowed for all admin users.
2. Backdated payments must be auditable.
3. The effective payment date and recorded timestamp should both be preserved.

### 8.7 Payment Deletion and Reversal

1. Ordinary deletion of payments should be disallowed.
2. If a payment was entered in error, the preferred action is reversal, voiding, or compensating correction.
3. Any reversal must be auditable.

## 9. Penalty Rules

### 9.1 Penalty Use in Version 1

1. Penalties are enabled in Version 1.
2. Penalties are implemented through a **late-charge mechanism** rather than as a simple administrative fee.
3. A late charge is a separate financial record linked to the overdue installment that triggered it.
4. The late charge amount is calculated as **10%** of the unpaid installment amount at the end of the grace period.
5. The late charge is treated as additional charge principal, and interest accrues on that amount according to the configured periodic interest model.
6. Late-charge creation and accrual must be auditable.

### 9.2 Penalty Trigger Rule

Recommended V1 rule:

* when an installment remains unpaid beyond the one-week grace period, a **one-time** late charge is created for that installment
* the late charge amount is calculated as **10%** of the unpaid installment balance at the end of the grace period
* the late charge is linked to the original installment that triggered it
* the late charge is treated as a separate charge balance for tracking, accrual, allocation, and reporting purposes
* only one late charge may be created for a given overdue installment event

### 9.3 Penalty Limits

1. Penalties must not be negative.
2. Penalty application must be auditable.
3. Because penalties behave as additional charge principal in Version 1, the system must clearly distinguish:

   * original loan principal
   * accrued regular interest
   * late-charge principal
   * accrued interest on late charges
4. The implementation must prevent hidden or duplicate late-charge creation for the same overdue event.
5. A late charge may be paid, partially paid, waived, or remain outstanding, but its history must remain traceable.

## 10. Balance Calculation Rules

### 10.1 Outstanding Balance Definition

The outstanding balance of a loan is the sum of:

* unpaid principal
* unpaid interest
* unpaid penalties

### 10.2 Balance Source of Truth

1. Loan balances must be derived from the repayment schedule and payment records.
2. The system should avoid storing independently editable balance fields that can drift from transaction history.
3. Any cached summary balance must be reproducible from underlying records.

### 10.3 Next Amount Due

The system should compute and display:

* the next due installment
* the amount currently due
* the total overdue amount
* the total remaining balance

## 11. Overdue and Arrears Rules

### 11.1 Overdue Determination

1. A schedule item does not become overdue immediately on its due date.
2. A schedule item becomes overdue only when its due date has passed by more than **one week** and it is not fully paid.
3. A loan becomes overdue when one or more schedule items are overdue.

### 11.2 Days Overdue

1. The system should calculate days overdue from the earliest unpaid overdue installment.
2. Days overdue should update automatically based on the current date.

### 11.3 Cure of Overdue Status

1. If all overdue installments are fully settled and future installments are not yet due, the loan may return from **overdue** to **active**.
2. If the full loan is settled, the status becomes **closed**.

## 12. Restructuring Rules

### 12.1 Version 1 Policy

1. Loan restructuring is not a core workflow for Version 1, but the status may exist for future compatibility.
2. If restructuring is implemented later, the original terms and revised terms must remain historically traceable.

## 13. Audit and History Rules

### 13.1 Auditable Actions

The following actions must be auditable:

* borrower creation and major edits
* loan creation
* loan status changes
* payment recording
* payment reversal or correction
* penalty application
* waiver actions
* restructuring actions

### 13.2 Audit Record Contents

An audit log entry should store:

* actor/user
* action type
* entity type
* entity identifier
* timestamp
* relevant before and after values when appropriate

### 13.3 Historical Preservation

1. Financial history should be append-oriented where possible.
2. Important records should not disappear without trace.
3. The system should preserve enough history to explain how a balance was reached.

## 14. Data Integrity Rules

1. Money values must not use floating-point arithmetic.
2. Required fields must be validated before records are saved.
3. Invalid statuses must not be accepted.
4. Foreign key relationships must be enforced.
5. The system should reject logically inconsistent records, such as a closed loan with unpaid installments.

## 15. Role and Permission Rules

### 15.1 Admin

An admin may:

* create and edit borrowers
* create and manage loans
* record and correct payments
* change statuses
* view reports
* manage staff users

### 15.2 Staff

A staff user may:

* view borrowers and loans
* record payments
* view reports allowed by policy

### 15.3 Restricted Actions

By default, only admin users should be able to:

* reverse or correct payments
* mark loans as defaulted or restructured
* waive penalties
* edit core loan terms after activation

## 16. Reporting Rules

1. Reports must reflect the same source-of-truth calculations as the loan detail pages.
2. The dashboard totals must be consistent with loan and payment data.
3. Overdue reports must be based on current unpaid overdue schedule items.

## 17. Version 1 Simplifications

To keep implementation realistic, Version 1 intentionally simplifies the following:

* flat-rate interest only
* weekly and monthly frequencies only
* fixed late penalties only
* internal users only
* no payment gateway integration
* no borrower self-service portal
* no automatic collections logic
* no multi-currency support

## 18. Finalized Numeric Policy Choices

The following numeric policy choices have been confirmed for Version 1:

1. Monthly periodic interest rate: **30%**
2. Weekly periodic interest rate: **8%**
3. Late-charge percentage: **10%** of the unpaid installment amount after the one-week grace period
4. Grace period before overdue status: **one week**
5. Overpayments: **not allowed**
6. Rounding tolerance: **none**

## 19. Implementation Consequences

These business rules imply the following technical requirements:

1. The data model must support borrowers, loans, schedule items, payments, late charges, users, and audit logs.
2. The payment allocation logic must be implemented centrally in backend business logic.
3. Loan balance calculations must be reproducible from transaction history.
4. Status transitions should be validated, not changed arbitrarily.
5. Unit tests must verify schedule generation, payment allocation, overdue detection, late-charge creation, and loan closure.
6. The system must preserve separate tracking for original principal, regular interest, late-charge principal, late-charge interest, paid amounts, and waived amounts.

---

This business rules document is intended to serve as the policy baseline for the Internal Loan Management System. It should be revised whenever core financial or operational rules change.
