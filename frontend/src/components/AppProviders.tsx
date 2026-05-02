"use client";

import { AuthProvider } from "@/components/AuthProvider";

export function AppProviders({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}
