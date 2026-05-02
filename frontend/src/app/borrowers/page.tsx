"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Plus, RotateCw } from "lucide-react";

import { useAuth } from "@/components/AuthProvider";
import { EmptyState } from "@/components/EmptyState";
import { Notice } from "@/components/Notice";
import { PageHeader } from "@/components/PageHeader";
import { ProtectedPage } from "@/components/ProtectedPage";
import { StatusBadge } from "@/components/StatusBadge";
import {
  createBorrower,
  listBorrowerLoans,
  listBorrowers
} from "@/lib/api";
import { formatDate, formatMoney } from "@/lib/format";
import type { Borrower, Loan } from "@/lib/types";

export default function BorrowersPage() {
  return (
    <ProtectedPage>
      <BorrowersContent />
    </ProtectedPage>
  );
}

function BorrowersContent() {
  const { token, user } = useAuth();
  const [borrowers, setBorrowers] = useState<Borrower[]>([]);
  const [selectedBorrowerId, setSelectedBorrowerId] = useState<string | null>(null);
  const [selectedLoans, setSelectedLoans] = useState<Loan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const refreshBorrowers = useCallback(async () => {
    if (!token) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      setBorrowers(await listBorrowers(token));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Borrowers load failed");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void refreshBorrowers();
  }, [refreshBorrowers]);

  const selectedBorrower = useMemo(
    () => borrowers.find((borrower) => borrower.id === selectedBorrowerId) ?? null,
    [borrowers, selectedBorrowerId]
  );

  async function handleCreateBorrower(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    const form = new FormData(event.currentTarget);
    setIsSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const borrower = await createBorrower(token, {
        full_name: String(form.get("full_name") ?? ""),
        phone_number: emptyToNull(form.get("phone_number")),
        external_id_number: emptyToNull(form.get("external_id_number")),
        address: emptyToNull(form.get("address")),
        notes: emptyToNull(form.get("notes")),
        status: "active"
      });
      event.currentTarget.reset();
      setBorrowers((current) => [borrower, ...current]);
      setSuccess(`Borrower created: ${borrower.full_name}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Borrower creation failed");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSelectBorrower(borrowerId: string) {
    if (!token) {
      return;
    }
    setSelectedBorrowerId(borrowerId);
    setError(null);
    try {
      setSelectedLoans(await listBorrowerLoans(token, borrowerId));
    } catch (caught) {
      setSelectedLoans([]);
      setError(caught instanceof Error ? caught.message : "Loan history load failed");
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow={user?.role === "admin" ? "Admin" : "Staff"}
        title="Borrowers"
        actions={
          <button className="secondary-button" onClick={refreshBorrowers} type="button">
            <RotateCw aria-hidden="true" size={16} />
            Refresh
          </button>
        }
      />

      {error ? <Notice tone="error">{error}</Notice> : null}
      {success ? <Notice tone="success">{success}</Notice> : null}

      <section className="two-column-layout">
        <form className="panel form-panel" onSubmit={handleCreateBorrower}>
          <div className="section-heading">
            <h2>New Borrower</h2>
            <p>Admin users can create borrower records.</p>
          </div>

          <label>
            <span>Full name</span>
            <input name="full_name" required />
          </label>

          <label>
            <span>Phone number</span>
            <input name="phone_number" />
          </label>

          <label>
            <span>External ID</span>
            <input name="external_id_number" />
          </label>

          <label>
            <span>Address</span>
            <input name="address" />
          </label>

          <label>
            <span>Notes</span>
            <textarea name="notes" rows={3} />
          </label>

          <button className="primary-button" disabled={isSaving} type="submit">
            <Plus aria-hidden="true" size={16} />
            {isSaving ? "Creating" : "Create borrower"}
          </button>
        </form>

        <section className="panel">
          <div className="section-heading">
            <h2>Borrower List</h2>
            <p>{isLoading ? "Loading records" : `${borrowers.length} records`}</p>
          </div>

          {borrowers.length === 0 && !isLoading ? (
            <EmptyState message="No borrowers found." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Phone</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {borrowers.map((borrower) => (
                    <tr
                      className={
                        borrower.id === selectedBorrowerId ? "selected-row" : undefined
                      }
                      key={borrower.id}
                      onClick={() => void handleSelectBorrower(borrower.id)}
                    >
                      <td>{borrower.full_name}</td>
                      <td>{borrower.phone_number ?? "Not set"}</td>
                      <td>
                        <StatusBadge status={borrower.status} />
                      </td>
                      <td>{formatDate(borrower.created_at.slice(0, 10))}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </section>

      <section className="panel">
        <div className="section-heading">
          <h2>Loan History</h2>
          <p>{selectedBorrower?.full_name ?? "Select a borrower"}</p>
        </div>

        {!selectedBorrower ? (
          <EmptyState message="Choose a borrower to view loan history." />
        ) : selectedLoans.length === 0 ? (
          <EmptyState message="No loans found for this borrower." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Start</th>
                  <th>Principal</th>
                  <th>Frequency</th>
                  <th>Status</th>
                  <th>End</th>
                </tr>
              </thead>
              <tbody>
                {selectedLoans.map((loan) => (
                  <tr key={loan.id}>
                    <td>{formatDate(loan.start_date)}</td>
                    <td>{formatMoney(loan.principal_amount)}</td>
                    <td>{loan.repayment_frequency}</td>
                    <td>
                      <StatusBadge status={loan.status} />
                    </td>
                    <td>{formatDate(loan.end_date)}</td>
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
