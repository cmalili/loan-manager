"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  AlertTriangle,
  Banknote,
  LayoutDashboard,
  LogOut,
  Receipt,
  Users
} from "lucide-react";

import { useAuth } from "@/components/AuthProvider";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/borrowers", label: "Borrowers", icon: Users },
  { href: "/loans", label: "Loans", icon: Banknote },
  { href: "/payments", label: "Payments", icon: Receipt },
  { href: "/overdue", label: "Overdue", icon: AlertTriangle }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true">
            LM
          </div>
          <div>
            <p className="brand-title">Loan Manager</p>
            <p className="brand-subtitle">Internal operations</p>
          </div>
        </div>

        <nav className="sidebar-nav" aria-label="Primary">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                aria-current={isActive ? "page" : undefined}
                className={isActive ? "nav-item active" : "nav-item"}
                href={item.href}
                key={item.href}
              >
                <Icon aria-hidden="true" size={18} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div>
            <p className="user-name">{user?.full_name ?? "Signed in"}</p>
            <p className="user-role">{user?.role ?? "user"}</p>
          </div>
          <button
            aria-label="Sign out"
            className="icon-button"
            onClick={handleLogout}
            title="Sign out"
            type="button"
          >
            <LogOut aria-hidden="true" size={18} />
          </button>
        </div>
      </aside>

      <main className="main-surface">{children}</main>
    </div>
  );
}
