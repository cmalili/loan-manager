"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, RotateCw } from "lucide-react";

import { useAuth } from "@/components/AuthProvider";
import { EmptyState } from "@/components/EmptyState";
import { Notice } from "@/components/Notice";
import { PageHeader } from "@/components/PageHeader";
import { ProtectedPage } from "@/components/ProtectedPage";
import { StatusBadge } from "@/components/StatusBadge";
import { listOverdueLoans } from "@/lib/api";
import { formatDate, formatMoney, todayIsoDate } from "@/lib/format";
import type { OverdueLoan } from "@/lib/types";

export default function OverduePage() {
  return (
    <ProtectedPage>
      <OverdueContent />
    </ProtectedPage>
  );
}

function OverdueContent() {
  const { token } = useAuth();
  const [asOfDate, setAsOfDate] = useState(todayIsoDate());
  const [rows, setRows] = useState<OverdueLoan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshOverdue = useCallback(async () => {
    if (!token) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      setRows(await listOverdueLoans(token, asOfDate));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Overdue load failed");
    } finally {
      setIsLoading(false);
    }
  }, [asOfDate, token]);

  useEffect(() => {
    void refreshOverdue();
  }, [refreshOverdue]);

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Collections"
        title="Overdue Loans"
        actions={
          <div className="toolbar">
            <input
              aria-label="As of date"
              onChange={(event) => setAsOfDate(event.target.value)}
              type="date"
              value={asOfDate}
            />
            <button className="secondary-button" onClick={refreshOverdue} type="button">
              <RotateCw aria-hidden="true" size={16} />
              Refresh
            </button>
          </div>
        }
      />

      {error ? <Notice tone="error">{error}</Notice> : null}

      <section className="panel">
        <div className="section-heading">
          <h2>Overdue Queue</h2>
          <p>{isLoading ? "Processing overdue state" : `${rows.length} loans`}</p>
        </div>

        {rows.length === 0 && !isLoading ? (
          <EmptyState message="No overdue loans for the selected date." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Borrower</th>
                  <th>Earliest due</th>
                  <th>Days</th>
                  <th>Installments</th>
                  <th>Regular balance</th>
                  <th>Late charges</th>
                  <th>Total</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.loan_id}>
                    <td>
                      <span className="row-title">
                        <AlertTriangle aria-hidden="true" size={16} />
                        {row.borrower_name}
                      </span>
                    </td>
                    <td>{formatDate(row.earliest_overdue_due_date)}</td>
                    <td>{row.days_overdue}</td>
                    <td>{row.overdue_installment_count}</td>
                    <td>{formatMoney(row.overdue_regular_balance)}</td>
                    <td>{formatMoney(row.outstanding_late_charge_balance)}</td>
                    <td>{formatMoney(row.total_overdue_balance)}</td>
                    <td>
                      <StatusBadge status={row.loan_status} />
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
