import type {
  Borrower,
  DashboardSummary,
  Loan,
  LoginResponse,
  OverdueLoan,
  Payment
} from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type ApiRequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  token?: string | null;
  body?: unknown;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function apiRequest<T>(
  path: string,
  { method = "GET", token, body }: ApiRequestOptions = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: body === undefined ? undefined : JSON.stringify(body)
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") {
        message = payload.detail;
      }
    } catch {
      // Keep the HTTP status message if the backend did not return JSON.
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/auth/login", {
    method: "POST",
    body: { email, password }
  });
}

export function getDashboardSummary(
  token: string,
  asOfDate: string
): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>(
    `/reports/dashboard-summary?as_of_date=${asOfDate}`,
    { token }
  );
}

export function listRecentPayments(
  token: string,
  limit = 10
): Promise<Payment[]> {
  return apiRequest<Payment[]>(`/reports/recent-payments?limit=${limit}`, { token });
}

export function listOverdueLoans(
  token: string,
  asOfDate: string
): Promise<OverdueLoan[]> {
  return apiRequest<OverdueLoan[]>(
    `/reports/overdue-loans?as_of_date=${asOfDate}`,
    { token }
  );
}

export function listBorrowers(token: string): Promise<Borrower[]> {
  return apiRequest<Borrower[]>("/borrowers/", { token });
}

export type CreateBorrowerPayload = {
  full_name: string;
  phone_number?: string | null;
  external_id_number?: string | null;
  address?: string | null;
  notes?: string | null;
  status?: "active" | "inactive";
};

export function createBorrower(
  token: string,
  payload: CreateBorrowerPayload
): Promise<Borrower> {
  return apiRequest<Borrower>("/borrowers/", {
    method: "POST",
    token,
    body: payload
  });
}

export function listBorrowerLoans(
  token: string,
  borrowerId: string
): Promise<Loan[]> {
  return apiRequest<Loan[]>(`/borrowers/${borrowerId}/loans`, { token });
}

export type CreateLoanPayload = {
  borrower_id: string;
  created_by_user_id: string;
  principal_amount: string;
  repayment_frequency: "weekly" | "monthly";
  term_length: number;
  start_date: string;
  status: "draft" | "active";
  grace_period_days: 7;
  notes?: string | null;
};

export function createLoan(
  token: string,
  payload: CreateLoanPayload
): Promise<Loan> {
  return apiRequest<Loan>("/loans/", {
    method: "POST",
    token,
    body: payload
  });
}

export type RecordPaymentPayload = {
  loan_id: string;
  borrower_id: string;
  recorded_by_user_id: string;
  amount: string;
  payment_date: string;
  payment_method?: string | null;
  reference_code?: string | null;
  notes?: string | null;
};

export function recordPayment(
  token: string,
  payload: RecordPaymentPayload
): Promise<Payment> {
  return apiRequest<Payment>("/payments/", {
    method: "POST",
    token,
    body: payload
  });
}
