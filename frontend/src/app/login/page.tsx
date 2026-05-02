"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LockKeyhole, Mail } from "lucide-react";

import { useAuth } from "@/components/AuthProvider";
import { Notice } from "@/components/Notice";

export default function LoginPage() {
  const router = useRouter();
  const { login, token, isReady } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isReady && token) {
      router.replace("/dashboard");
    }
  }, [isReady, router, token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-screen">
      <section className="login-panel" aria-labelledby="login-title">
        <div className="login-brand">
          <div className="brand-mark large" aria-hidden="true">
            LM
          </div>
          <div>
            <p className="eyebrow">Internal tool</p>
            <h1 id="login-title">Loan Manager</h1>
          </div>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            <span>Email</span>
            <div className="input-with-icon">
              <Mail aria-hidden="true" size={18} />
              <input
                autoComplete="email"
                name="email"
                onChange={(event) => setEmail(event.target.value)}
                required
                type="email"
                value={email}
              />
            </div>
          </label>

          <label>
            <span>Password</span>
            <div className="input-with-icon">
              <LockKeyhole aria-hidden="true" size={18} />
              <input
                autoComplete="current-password"
                name="password"
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
            </div>
          </label>

          {error ? <Notice tone="error">{error}</Notice> : null}

          <button className="primary-button" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Signing in" : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
