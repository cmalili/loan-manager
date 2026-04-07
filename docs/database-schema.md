# Loan Management App Database Schema (Version 1)

## 1. Purpose

This document translates the ER diagram and business rules into a concrete relational database schema for Version 1 of the Internal Loan Management System.

This schema is designed for PostgreSQL and aims to be:

* correct for financial tracking
* auditable
* maintainable
* reasonably normalized
* practical for implementation with FastAPI and PostgreSQL

---

## 2. Design Principles

### 2.1 Money Representation

Money values must not use floating point.

All money fields should use a fixed-precision numeric type, for example:

* `NUMERIC(12,2)`

If the application later needs smaller currency units or higher precision, this can be revised.

### 2.2 Timestamps

All major tables should include timestamps such as:

* `created_at`
* `updated_at`

### 2.3 IDs

For Version 1, the schema will use:

* `UUID` primary keys

This is a good fit for modern backend systems and avoids predictable sequential identifiers in external APIs.

### 2.4 Source of Truth

Balances should not be stored as freely editable summary fields.

The source of truth should be:

* repayment schedule items
* payments
* payment allocations
* late charges
* waivers

Any summary balances shown in the UI should be derived from these records.

---

## 3. Recommended PostgreSQL Setup

Recommended PostgreSQL extension:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

This allows use of:

* `gen_random_uuid()`

---

## 4. Table Overview

The core Version 1 tables are:

1. `users`
2. `borrowers`
3. `loans`
4. `repayment_schedule_items`
5. `late_charges`
6. `payments`
7. `payment_allocations`
8. `audit_logs`

---

## 5. Enumerated Value Sets

For Version 1, these values can be implemented either as PostgreSQL enums or as text columns with application-level validation plus database check constraints.

For simplicity and easier migrations, this design assumes:

* `TEXT` fields with controlled allowed values

### 5.1 user_role

Allowed values:

* `admin`
* `staff`

### 5.2 borrower_status

Allowed values:

* `active`
* `inactive`

### 5.3 loan_status

Allowed values:

* `draft`
* `active`
* `closed`
* `overdue`
* `defaulted`
* `restructured`
* `cancelled`

### 5.4 repayment_frequency

Allowed values:

* `weekly`
* `monthly`

### 5.5 schedule_item_status

Allowed values:

* `pending`
* `partially_paid`
* `paid`
* `overdue`
* `waived`

### 5.6 payment_status

Allowed values:

* `recorded`
* `voided`
* `reversed`

### 5.7 late_charge_status

Allowed values:

* `outstanding`
* `partially_paid`
* `paid`
* `waived`
* `voided`

### 5.8 payment_allocation_type

Allowed values:

* `late_charge_interest`
* `late_charge_principal`
* `regular_interest`
* `regular_principal`

---

## 6. Table Definitions

## 6.1 `users`

Represents internal system users.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'staff')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Notes

* `email` is unique.
* password hashes only; never store raw passwords.

---

## 6.2 `borrowers`

Represents borrowers.

```sql
CREATE TABLE borrowers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    phone_number TEXT,
    external_id_number TEXT,
    address TEXT,
    notes TEXT,
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Notes

* `external_id_number` is not marked unique yet because real-world identity quality may vary. This can be tightened later if required.
* A borrower should not be physically deleted if they have historical loans.

---

## 6.3 `loans`

Represents loans issued to borrowers.

```sql
CREATE TABLE loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    borrower_id UUID NOT NULL REFERENCES borrowers(id),
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    principal_amount NUMERIC(12,2) NOT NULL CHECK (principal_amount > 0),
    repayment_frequency TEXT NOT NULL CHECK (repayment_frequency IN ('weekly', 'monthly')),
    periodic_interest_rate NUMERIC(5,2) NOT NULL CHECK (periodic_interest_rate >= 0),
    term_length INTEGER NOT NULL CHECK (term_length > 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('draft', 'active', 'closed', 'overdue', 'defaulted', 'restructured', 'cancelled')
    ),
    grace_period_days INTEGER NOT NULL DEFAULT 7 CHECK (grace_period_days >= 0),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (end_date >= start_date)
);
```

### Notes

* `periodic_interest_rate` stores the rate for the actual repayment frequency used by that loan.

  * monthly loans: `30.00`
  * weekly loans: `8.00`
* one borrower may have many historical loans, but only one active loan in V1.

### Constraint for one active loan per borrower

Use a partial unique index:

```sql
CREATE UNIQUE INDEX uq_loans_one_active_per_borrower
ON loans (borrower_id)
WHERE status = 'active';
```

---

## 6.4 `repayment_schedule_items`

Represents each installment of a loan.

```sql
CREATE TABLE repayment_schedule_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    installment_number INTEGER NOT NULL CHECK (installment_number > 0),
    due_date DATE NOT NULL,
    principal_due NUMERIC(12,2) NOT NULL CHECK (principal_due >= 0),
    interest_due NUMERIC(12,2) NOT NULL CHECK (interest_due >= 0),
    principal_paid NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (principal_paid >= 0),
    interest_paid NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (interest_paid >= 0),
    waived_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (waived_amount >= 0),
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'partially_paid', 'paid', 'overdue', 'waived')
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (loan_id, installment_number)
);
```

### Notes

* one loan has many schedule items.
* `principal_paid` and `interest_paid` are stored because they are not arbitrary summaries; they reflect allocated payment totals and make status checks efficient.
* total due for an installment is:

  * `principal_due + interest_due`
* remaining installment balance is derived.

---

## 6.5 `late_charges`

Represents the one-time late charge triggered by an overdue installment after the grace period.

```sql
CREATE TABLE late_charges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    schedule_item_id UUID NOT NULL REFERENCES repayment_schedule_items(id) ON DELETE CASCADE,
    created_by_user_id UUID REFERENCES users(id),
    trigger_date DATE NOT NULL,
    base_unpaid_amount NUMERIC(12,2) NOT NULL CHECK (base_unpaid_amount >= 0),
    charge_rate NUMERIC(5,2) NOT NULL CHECK (charge_rate >= 0),
    charge_principal_amount NUMERIC(12,2) NOT NULL CHECK (charge_principal_amount >= 0),
    accrued_interest_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (accrued_interest_amount >= 0),
    principal_paid NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (principal_paid >= 0),
    interest_paid NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (interest_paid >= 0),
    waived_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (waived_amount >= 0),
    status TEXT NOT NULL CHECK (
        status IN ('outstanding', 'partially_paid', 'paid', 'waived', 'voided')
    ),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (schedule_item_id)
);
```

### Notes

* `UNIQUE (schedule_item_id)` enforces the Version 1 rule of at most one late charge per schedule item.
* `charge_rate` should be `10.00` in Version 1.
* `accrued_interest_amount` represents interest accrued on the late-charge principal.

---

## 6.6 `payments`

Represents payments recorded against loans.

```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE RESTRICT,
    borrower_id UUID NOT NULL REFERENCES borrowers(id) ON DELETE RESTRICT,
    recorded_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    payment_date DATE NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payment_method TEXT,
    reference_code TEXT,
    notes TEXT,
    is_backdated BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL CHECK (status IN ('recorded', 'voided', 'reversed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Notes

* `borrower_id` is somewhat redundant because it can be inferred through `loan_id`, but keeping it can simplify reporting and integrity checks.
* application logic should verify that `payments.borrower_id` matches `loans.borrower_id`.
* raw deletion should not be used; use reversal or voiding.

---

## 6.7 `payment_allocations`

Represents how a payment is split across different obligations.

```sql
CREATE TABLE payment_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    schedule_item_id UUID REFERENCES repayment_schedule_items(id) ON DELETE CASCADE,
    late_charge_id UUID REFERENCES late_charges(id) ON DELETE CASCADE,
    allocation_type TEXT NOT NULL CHECK (
        allocation_type IN (
            'late_charge_interest',
            'late_charge_principal',
            'regular_interest',
            'regular_principal'
        )
    ),
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        (schedule_item_id IS NOT NULL AND late_charge_id IS NULL)
        OR
        (schedule_item_id IS NULL AND late_charge_id IS NOT NULL)
    )
);
```

### Notes

* each allocation belongs to exactly one payment.
* an allocation points to either:

  * a schedule item
  * or a late charge
* this is what makes payment application auditable.

### Important application-level rule

For each `payment_id`:

* sum of all `payment_allocations.amount` must equal `payments.amount`

This is difficult to enforce with a simple table constraint and is better enforced in service logic plus tests.

---

## 6.8 `audit_logs`

Represents auditable history.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    action_type TEXT NOT NULL,
    before_state_json JSONB,
    after_state_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Notes

* `entity_type` examples:

  * `borrower`
  * `loan`
  * `payment`
  * `late_charge`
* `action_type` examples:

  * `create`
  * `update`
  * `status_change`
  * `void`
  * `reverse`
  * `waive`

---

## 7. Recommended Indexes

```sql
CREATE INDEX idx_borrowers_full_name ON borrowers (full_name);
CREATE INDEX idx_borrowers_phone_number ON borrowers (phone_number);

CREATE INDEX idx_loans_borrower_id ON loans (borrower_id);
CREATE INDEX idx_loans_status ON loans (status);
CREATE INDEX idx_loans_start_date ON loans (start_date);
CREATE INDEX idx_loans_end_date ON loans (end_date);

CREATE INDEX idx_schedule_items_loan_id ON repayment_schedule_items (loan_id);
CREATE INDEX idx_schedule_items_due_date ON repayment_schedule_items (due_date);
CREATE INDEX idx_schedule_items_status ON repayment_schedule_items (status);

CREATE INDEX idx_late_charges_loan_id ON late_charges (loan_id);
CREATE INDEX idx_late_charges_status ON late_charges (status);
CREATE INDEX idx_late_charges_trigger_date ON late_charges (trigger_date);

CREATE INDEX idx_payments_loan_id ON payments (loan_id);
CREATE INDEX idx_payments_borrower_id ON payments (borrower_id);
CREATE INDEX idx_payments_payment_date ON payments (payment_date);
CREATE INDEX idx_payments_status ON payments (status);
CREATE INDEX idx_payments_reference_code ON payments (reference_code);

CREATE INDEX idx_payment_allocations_payment_id ON payment_allocations (payment_id);
CREATE INDEX idx_payment_allocations_loan_id ON payment_allocations (loan_id);
CREATE INDEX idx_payment_allocations_schedule_item_id ON payment_allocations (schedule_item_id);
CREATE INDEX idx_payment_allocations_late_charge_id ON payment_allocations (late_charge_id);

CREATE INDEX idx_audit_logs_entity ON audit_logs (entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs (created_at);
```

---

## 8. Constraints That Should Live Mostly in Application Logic

Some rules are real business rules but are awkward to enforce purely with simple SQL constraints.

These should be enforced in backend service logic and covered by tests:

1. the payment’s borrower must match the loan’s borrower
2. total payment allocations must equal the payment amount
3. overpayments are not allowed
4. loan status transitions must be valid
5. overdue status changes should reflect due dates and grace periods
6. late charges should be created only after the grace period
7. late charge amount should equal 10% of unpaid installment amount at trigger time
8. monthly loans must use 30% rate and weekly loans must use 8% rate in Version 1

---

## 9. Derived Values That Should Not Be Stored as Freely Editable Fields

The following should usually be computed from underlying records rather than stored as arbitrary state:

* loan outstanding principal
* loan outstanding interest
* loan outstanding late-charge principal
* loan outstanding late-charge interest
* total overdue amount
* next amount due
* total remaining balance

These should be derived from:

* repayment schedule items
* late charges
* payments
* payment allocations
* waivers

---

## 10. Important Schema Tradeoffs

### 10.1 Why keep `borrower_id` on `payments`?

Strict normalization would allow deriving borrower through `loan_id`.

However, keeping `borrower_id` on payments helps with:

* reporting
* integrity checks
* easier filtering

This is acceptable as long as application logic guarantees consistency.

### 10.2 Why store `principal_paid` and `interest_paid` on schedule items?

These are technically derivable from payment allocations, but storing them can improve query simplicity and status updates.

This is acceptable if:

* allocations remain the deeper source of truth
* service logic updates both consistently

### 10.3 Why use a separate `payment_allocations` table?

Because one payment may be split across:

* late-charge interest
* late-charge principal
* regular interest
* regular principal

Without this table, the financial history becomes much harder to explain and audit.

---

## 11. Recommended Next Step After Schema Design

After approving this schema, the next deliverable should be one of these:

1. SQL migration files
2. SQLAlchemy ORM models
3. FastAPI Pydantic schemas

The best immediate next step is usually:

* create SQLAlchemy models from this schema
* then generate migrations with Alembic

---

This document is the Version 1 database schema baseline for the Internal Loan Management System.
