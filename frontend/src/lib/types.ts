export type UserRole = "admin" | "staff";

export type AuthenticatedUser = {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  user: AuthenticatedUser;
};

export type BorrowerStatus = "active" | "inactive";

export type Borrower = {
  id: string;
  full_name: string;
  phone_number: string | null;
  external_id_number: string | null;
  address: string | null;
  notes: string | null;
  status: BorrowerStatus;
  created_at: string;
  updated_at: string;
};

export type RepaymentFrequency = "weekly" | "monthly";

export type LoanStatus =
  | "draft"
  | "active"
  | "closed"
  | "overdue"
  | "defaulted"
  | "restructured"
  | "cancelled";

export type Loan = {
  id: string;
  borrower_id: string;
  created_by_user_id: string;
  principal_amount: string;
  repayment_frequency: RepaymentFrequency;
  periodic_interest_rate: string;
  term_length: number;
  start_date: string;
  end_date: string;
  status: LoanStatus;
  grace_period_days: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type PaymentAllocationType =
  | "late_charge_interest"
  | "late_charge_principal"
  | "regular_interest"
  | "regular_principal";

export type PaymentAllocation = {
  id: string;
  payment_id: string;
  loan_id: string;
  schedule_item_id: string | null;
  late_charge_id: string | null;
  allocation_type: PaymentAllocationType;
  amount: string;
  created_at: string;
};

export type Payment = {
  id: string;
  loan_id: string;
  borrower_id: string;
  recorded_by_user_id: string;
  amount: string;
  payment_date: string;
  recorded_at: string;
  payment_method: string | null;
  reference_code: string | null;
  notes: string | null;
  is_backdated: boolean;
  status: "recorded" | "voided" | "reversed";
  created_at: string;
  updated_at: string;
  allocations: PaymentAllocation[];
};

export type DashboardSummary = {
  active_loan_count: number;
  closed_loan_count: number;
  overdue_loan_count: number;
  total_outstanding_balance: string;
  total_overdue_balance: string;
  recent_payment_count: number;
  recent_payment_total: string;
};

export type OverdueLoan = {
  loan_id: string;
  borrower_id: string;
  borrower_name: string;
  loan_status: LoanStatus;
  earliest_overdue_due_date: string;
  days_overdue: number;
  overdue_installment_count: number;
  overdue_regular_balance: string;
  outstanding_late_charge_balance: string;
  total_overdue_balance: string;
};
