"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Banknote, CheckCircle2, Receipt } from "lucide-react";

import { ProtectedPage } from "@/components/ProtectedPage";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { Notice } from "@/components/Notice";
import { StatusBadge } from "@/components/StatusBadge";
import { getDashboardSummary, listRecentPayments } from "@/lib/api";
import { formatDate, formatMoney, todayIsoDate } from "@/lib/format";
import type { DashboardSummary, Payment } from "@/lib/types";
import { useAuth } from "@/components/AuthProvider";

const metricIcons = [Banknote, AlertTriangle, Receipt, CheckCircle2];

export default function DashboardPage() {
  return (
    <ProtectedPage>
      <DashboardContent />
    </ProtectedPage>
  );
}

function DashboardContent() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [recentPayments, setRecentPayments] = useState<Payment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }
    const authToken = token;

    async function loadDashboard() {
      setIsLoading(true);
      setError(null);
      try {
        const asOfDate = todayIsoDate();
        const [summaryResult, recentResult] = await Promise.all([
          getDashboardSummary(authToken, asOfDate),
          listRecentPayments(authToken, 8)
        ]);
        setSummary(summaryResult);
        setRecentPayments(recentResult);
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Dashboard load failed");
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, [token]);

  const metrics = [
    {
      label: "Outstanding",
      value: formatMoney(summary?.total_outstanding_balance),
      detail: `${summary?.active_loan_count ?? 0} active loans`
    },
    {
      label: "Overdue",
      value: formatMoney(summary?.total_overdue_balance),
      detail: `${summary?.overdue_loan_count ?? 0} overdue loans`
    },
    {
      label: "Recent payments",
      value: formatMoney(summary?.recent_payment_total),
      detail: `${summary?.recent_payment_count ?? 0} recorded recently`
    },
    {
      label: "Closed loans",
      value: String(summary?.closed_loan_count ?? 0),
      detail: "Fully settled"
    }
  ];

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Today" title="Dashboard" />

      {error ? <Notice tone="error">{error}</Notice> : null}

      <section className="metric-grid" aria-label="Dashboard metrics">
        {metrics.map((metric, index) => {
          const Icon = metricIcons[index];
          return (
            <article className="metric-card" key={metric.label}>
              <div className="metric-icon">
                <Icon aria-hidden="true" size={20} />
              </div>
              <div>
                <p>{metric.label}</p>
                <strong>{isLoading ? "..." : metric.value}</strong>
                <span>{metric.detail}</span>
              </div>
            </article>
          );
        })}
      </section>

      <section className="panel">
        <div className="section-heading">
          <h2>Recent Payments</h2>
          <p>Latest recorded repayment activity</p>
        </div>

        {recentPayments.length === 0 && !isLoading ? (
          <EmptyState message="No payments have been recorded yet." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Payment date</th>
                  <th>Amount</th>
                  <th>Method</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recentPayments.map((payment) => (
                  <tr key={payment.id}>
                    <td>{formatDate(payment.payment_date)}</td>
                    <td>{formatMoney(payment.amount)}</td>
                    <td>{payment.payment_method ?? "Not set"}</td>
                    <td>
                      <StatusBadge status={payment.status} />
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
