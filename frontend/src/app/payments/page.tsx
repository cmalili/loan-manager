"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { ReceiptText } from "lucide-react";

import { useAuth } from "@/components/AuthProvider";
import { EmptyState } from "@/components/EmptyState";
import { Notice } from "@/components/Notice";
import { PageHeader } from "@/components/PageHeader";
import { ProtectedPage } from "@/components/ProtectedPage";
import { StatusBadge } from "@/components/StatusBadge";
import { listBorrowerLoans, listBorrowers, recordPayment } from "@/lib/api";
import { formatDate, formatMoney, titleCase, todayIsoDate } from "@/lib/format";
import type { Borrower, Loan, Payment } from "@/lib/types";

export default function PaymentsPage() {
  return (
    <ProtectedPage>
      <PaymentsContent />
    </ProtectedPage>
  );
}

function PaymentsContent() {
  const { token, user } = useAuth();
  const [borrowers, setBorrowers] = useState<Borrower[]>([]);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [selectedBorrowerId, setSelectedBorrowerId] = useState("");
  const [selectedLoanId, setSelectedLoanId] = useState("");
  const [lastPayment, setLastPayment] = useState<Payment | null>(null);
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
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Borrowers load failed");
      } finally {
        setIsLoading(false);
      }
    }

    void loadBorrowers();
  }, [token]);

  const selectedLoan = useMemo(
    () => loans.find((loan) => loan.id === selectedLoanId) ?? null,
    [loans, selectedLoanId]
  );

  async function handleBorrowerChange(borrowerId: string) {
    setSelectedBorrowerId(borrowerId);
    setSelectedLoanId("");
    setLoans([]);

    if (!token || !borrowerId) {
      return;
    }

    try {
      const result = await listBorrowerLoans(token, borrowerId);
      setLoans(result.filter((loan) => loan.status !== "cancelled"));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Loan history load failed");
    }
  }

  async function handleRecordPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !user) {
      return;
    }

    const form = new FormData(event.currentTarget);
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    setLastPayment(null);

    try {
      const payment = await recordPayment(token, {
        loan_id: String(form.get("loan_id") ?? ""),
        borrower_id: selectedBorrowerId,
        recorded_by_user_id: user.id,
        amount: String(form.get("amount") ?? ""),
        payment_date: String(form.get("payment_date") ?? todayIsoDate()),
        payment_method: emptyToNull(form.get("payment_method")),
        reference_code: emptyToNull(form.get("reference_code")),
        notes: emptyToNull(form.get("notes"))
      });
      setLastPayment(payment);
      setSuccess("Payment recorded");
      event.currentTarget.reset();
      setSelectedLoanId("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Payment recording failed");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Repayments" title="Payments" />

      {error ? <Notice tone="error">{error}</Notice> : null}
      {success ? <Notice tone="success">{success}</Notice> : null}

      <section className="two-column-layout">
        <form className="panel form-panel" onSubmit={handleRecordPayment}>
          <div className="section-heading">
            <h2>Record Payment</h2>
            <p>Allocations are applied by backend financial rules.</p>
          </div>

          <label>
            <span>Borrower</span>
            <select
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
            <span>Loan</span>
            <select
              disabled={loans.length === 0}
              name="loan_id"
              onChange={(event) => setSelectedLoanId(event.target.value)}
              required
              value={selectedLoanId}
            >
              <option value="">
                {isLoading ? "Loading" : "Select loan"}
              </option>
              {loans.map((loan) => (
                <option key={loan.id} value={loan.id}>
                  {formatMoney(loan.principal_amount)} - {loan.status}
                </option>
              ))}
            </select>
          </label>

          <div className="field-grid">
            <label>
              <span>Amount</span>
              <input
                inputMode="decimal"
                min="0.01"
                name="amount"
                required
                step="0.01"
                type="number"
              />
            </label>

            <label>
              <span>Payment date</span>
              <input
                defaultValue={todayIsoDate()}
                name="payment_date"
                required
                type="date"
              />
            </label>
          </div>

          <div className="field-grid">
            <label>
              <span>Method</span>
              <input name="payment_method" placeholder="Cash" />
            </label>

            <label>
              <span>Reference</span>
              <input name="reference_code" />
            </label>
          </div>

          <label>
            <span>Notes</span>
            <textarea name="notes" rows={3} />
          </label>

          <button className="primary-button" disabled={isSaving} type="submit">
            <ReceiptText aria-hidden="true" size={16} />
            {isSaving ? "Recording" : "Record payment"}
          </button>
        </form>

        <section className="panel">
          <div className="section-heading">
            <h2>Selected Loan</h2>
            <p>Payment target</p>
          </div>

          {!selectedLoan ? (
            <EmptyState message="Select a borrower and loan." />
          ) : (
            <div className="detail-list">
              <div>
                <span>Principal</span>
                <strong>{formatMoney(selectedLoan.principal_amount)}</strong>
              </div>
              <div>
                <span>Rate</span>
                <strong>{selectedLoan.periodic_interest_rate}%</strong>
              </div>
              <div>
                <span>Frequency</span>
                <strong>{titleCase(selectedLoan.repayment_frequency)}</strong>
              </div>
              <div>
                <span>Status</span>
                <StatusBadge status={selectedLoan.status} />
              </div>
              <div>
                <span>Start</span>
                <strong>{formatDate(selectedLoan.start_date)}</strong>
              </div>
              <div>
                <span>End</span>
                <strong>{formatDate(selectedLoan.end_date)}</strong>
              </div>
            </div>
          )}
        </section>
      </section>

      <section className="panel">
        <div className="section-heading">
          <h2>Latest Allocation</h2>
          <p>{lastPayment ? formatMoney(lastPayment.amount) : "No payment recorded"}</p>
        </div>

        {!lastPayment ? (
          <EmptyState message="Recorded payment allocations will appear here." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Target</th>
                </tr>
              </thead>
              <tbody>
                {lastPayment.allocations.map((allocation) => (
                  <tr key={allocation.id}>
                    <td>{titleCase(allocation.allocation_type)}</td>
                    <td>{formatMoney(allocation.amount)}</td>
                    <td>
                      {allocation.late_charge_id ? "Late charge" : "Installment"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function emptyToNull(value: FormDataEntryValue | null): string | null {
  const text = String(value ?? "").trim();
  return text.length > 0 ? text : null;
}
