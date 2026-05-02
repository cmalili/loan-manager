"use client";

import { FormEvent, useEffect, useState } from "react";
import { Banknote, CalendarDays } from "lucide-react";

import { useAuth } from "@/components/AuthProvider";
import { EmptyState } from "@/components/EmptyState";
import { Notice } from "@/components/Notice";
import { PageHeader } from "@/components/PageHeader";
import { ProtectedPage } from "@/components/ProtectedPage";
import { StatusBadge } from "@/components/StatusBadge";
import { createLoan, listBorrowerLoans, listBorrowers } from "@/lib/api";
import { formatDate, formatMoney, todayIsoDate } from "@/lib/format";
import type { Borrower, Loan } from "@/lib/types";

export default function LoansPage() {
  return (
    <ProtectedPage>
      <LoansContent />
    </ProtectedPage>
  );
}

function LoansContent() {
  const { token, user } = useAuth();
  const [borrowers, setBorrowers] = useState<Borrower[]>([]);
  const [borrowerLoans, setBorrowerLoans] = useState<Loan[]>([]);
  const [selectedBorrowerId, setSelectedBorrowerId] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    const authToken = token;

    async function loadBorrowers() {
      setIsLoading(true);
      setError(null);
      try {
        const result = await listBorrowers(authToken);
        setBorrowers(result);
        if (result[0]) {
          setSelectedBorrowerId(result[0].id);
          setBorrowerLoans(await listBorrowerLoans(authToken, result[0].id));
        }
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Borrowers load failed");
      } finally {
        setIsLoading(false);
      }
    }

    void loadBorrowers();
  }, [token]);

  async function handleBorrowerChange(borrowerId: string) {
    setSelectedBorrowerId(borrowerId);
    setBorrowerLoans([]);
    if (!token || !borrowerId) {
      return;
    }

    try {
      setBorrowerLoans(await listBorrowerLoans(token, borrowerId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Loan history load failed");
    }
  }

  async function handleCreateLoan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !user) {
      return;
    }

    const form = new FormData(event.currentTarget);
    setIsSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const loan = await createLoan(token, {
        borrower_id: String(form.get("borrower_id") ?? ""),
        created_by_user_id: user.id,
        principal_amount: String(form.get("principal_amount") ?? ""),
        repayment_frequency: String(
          form.get("repayment_frequency") ?? "weekly"
        ) as "weekly" | "monthly",
        term_length: Number(form.get("term_length") ?? 1),
        start_date: String(form.get("start_date") ?? todayIsoDate()),
        status: String(form.get("status") ?? "draft") as "draft" | "active",
        grace_period_days: 7,
        notes: emptyToNull(form.get("notes"))
      });
      setSuccess("Loan created");
      if (loan.borrower_id === selectedBorrowerId) {
        setBorrowerLoans((current) => [loan, ...current]);
      }
      event.currentTarget.reset();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Loan creation failed");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Origination" title="Loans" />

      {error ? <Notice tone="error">{error}</Notice> : null}
      {success ? <Notice tone="success">{success}</Notice> : null}

      <section className="two-column-layout">
        <form className="panel form-panel" onSubmit={handleCreateLoan}>
          <div className="section-heading">
            <h2>Create Loan</h2>
            <p>Standard rates are applied by repayment frequency.</p>
          </div>

          <label>
            <span>Borrower</span>
            <select
              name="borrower_id"
              onChange={(event) => void handleBorrowerChange(event.target.value)}
              required
              value={selectedBorrowerId}
            >
              <option value="">Select borrower</option>
              {borrowers.map((borrower) => (
                <option key={borrower.id} value={borrower.id}>
                  {borrower.full_name}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Principal amount</span>
            <input
              inputMode="decimal"
              min="0.01"
              name="principal_amount"
              required
              step="0.01"
              type="number"
            />
          </label>

          <div className="field-grid">
            <label>
              <span>Frequency</span>
              <select name="repayment_frequency" required>
                <option value="weekly">Weekly, 8%</option>
                <option value="monthly">Monthly, 30%</option>
              </select>
            </label>

            <label>
              <span>Term length</span>
              <input min="1" name="term_length" required type="number" />
            </label>
          </div>

          <div className="field-grid">
            <label>
              <span>Start date</span>
              <input
                defaultValue={todayIsoDate()}
                name="start_date"
                required
                type="date"
              />
            </label>

            <label>
              <span>Status</span>
              <select name="status" required>
                <option value="draft">Draft</option>
                <option value="active">Active</option>
              </select>
            </label>
          </div>

          <label>
            <span>Notes</span>
            <textarea name="notes" rows={3} />
          </label>

          <button className="primary-button" disabled={isSaving} type="submit">
            <Banknote aria-hidden="true" size={16} />
            {isSaving ? "Creating" : "Create loan"}
          </button>
        </form>

        <section className="panel">
          <div className="section-heading">
            <h2>Borrower Loans</h2>
            <p>{isLoading ? "Loading borrowers" : "Selected borrower history"}</p>
          </div>

          {borrowerLoans.length === 0 ? (
            <EmptyState message="No loans to show for the selected borrower." />
          ) : (
            <div className="record-list">
              {borrowerLoans.map((loan) => (
                <article className="record-row" key={loan.id}>
                  <div className="record-icon">
                    <CalendarDays aria-hidden="true" size={18} />
                  </div>
                  <div>
                    <strong>{formatMoney(loan.principal_amount)}</strong>
                    <span>
                      {formatDate(loan.start_date)} to {formatDate(loan.end_date)}
                    </span>
                  </div>
                  <StatusBadge status={loan.status} />
                </article>
              ))}
            </div>
          )}
        </section>
      </section>
    </div>
  );
}

function emptyToNull(value: FormDataEntryValue | null): string | null {
  const text = String(value ?? "").trim();
  return text.length > 0 ? text : null;
}
