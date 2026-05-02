"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { useAuth } from "@/components/AuthProvider";

export function ProtectedPage({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { token, isReady } = useAuth();

  useEffect(() => {
    if (isReady && !token) {
      router.replace("/login");
    }
  }, [isReady, router, token]);

  if (!isReady || !token) {
    return (
      <main className="route-fallback">
        <div className="spinner" />
      </main>
    );
  }

  return <AppShell>{children}</AppShell>;
}
