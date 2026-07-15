"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "../../lib/api";
import { setSession } from "../../lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    setError(null);
    try {
      const auth =
        mode === "login"
          ? await login(email.trim(), password)
          : await register(email.trim(), password);
      setSession(auth.access_token, email.trim());
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setSubmitting(false);
    }
  }

  return (
    <main className="page narrow">
      <h1 className="page-title">
        {mode === "login" ? "Log in" : "Create an account"}
      </h1>
      <p className="page-subtitle">
        {mode === "login"
          ? "Log in to raise and track your tickets."
          : "Register to start raising tickets."}
      </p>

      <div className="card">
        <form className="form" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jane@example.com"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === "register" ? "At least 8 characters" : ""}
              minLength={mode === "register" ? 8 : undefined}
              required
            />
          </div>

          {error && <div className="error-box">{error}</div>}

          <button className="btn-primary" type="submit" disabled={submitting}>
            {submitting
              ? "Please wait…"
              : mode === "login"
                ? "Log in"
                : "Register"}
          </button>
        </form>
      </div>

      <p className="page-subtitle" style={{ marginTop: 16 }}>
        {mode === "login" ? (
          <>
            Don&apos;t have an account?{" "}
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                setMode("register");
                setError(null);
              }}
            >
              Register
            </a>
          </>
        ) : (
          <>
            Already have an account?{" "}
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                setMode("login");
                setError(null);
              }}
            >
              Log in
            </a>
          </>
        )}
      </p>
    </main>
  );
}
