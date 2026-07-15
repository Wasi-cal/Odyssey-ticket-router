"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthError, createTicket } from "../lib/api";
import { getToken } from "../lib/auth";

export default function RaiseTicketPage() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const body = text.trim();
    if (!body || submitting) return;

    setSubmitting(true);
    setError(null);
    try {
      const ticket = await createTicket(body);
      router.push(
        ticket.ticket_ref
          ? `/tickets/${encodeURIComponent(ticket.ticket_ref)}`
          : "/tickets",
      );
    } catch (err) {
      if (err instanceof AuthError) {
        router.replace("/login");
        return;
      }
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setSubmitting(false);
    }
  }

  return (
    <main className="page narrow">
      <h1 className="page-title">Raise a ticket</h1>
      <p className="page-subtitle">
        Describe the problem and it will be routed to the right team.
      </p>

      <div className="card">
        <form className="form" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="ticket-text">What's the issue?</label>
            <textarea
              id="ticket-text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="I was charged twice this month, please refund the duplicate."
              required
            />
          </div>

          {error && <div className="error-box">{error}</div>}

          <button className="btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Submitting…" : "Submit ticket"}
          </button>
        </form>
      </div>
    </main>
  );
}
