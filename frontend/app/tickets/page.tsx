"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthError, fetchTickets, type TicketSummary } from "../../lib/api";
import { getToken, getUserEmail } from "../../lib/auth";
import { relativeTime } from "../../lib/format";
import { PriorityBadge, StatusBadge } from "../../components/Badge";

type State =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; tickets: TicketSummary[] };

export default function MyTicketsPage() {
  const router = useRouter();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    fetchTickets()
      .then((tickets) => setState({ kind: "ready", tickets }))
      .catch((err) => {
        if (err instanceof AuthError) {
          router.replace("/login");
          return;
        }
        setState({
          kind: "error",
          message: err instanceof Error ? err.message : "Failed to load tickets.",
        });
      });
  }, [router]);

  return (
    <main className="page">
      <h1 className="page-title">My tickets</h1>
      <p className="page-subtitle">
        {getUserEmail() ? `Submitted by ${getUserEmail()}` : " "}
      </p>

      <div className="card">
        {state.kind === "loading" && <div className="state">Loading tickets…</div>}

        {state.kind === "error" && (
          <div className="state">
            <div className="error-box">{state.message}</div>
          </div>
        )}

        {state.kind === "ready" && state.tickets.length === 0 && (
          <div className="state">
            No tickets yet. <Link href="/">Raise one</Link>.
          </div>
        )}

        {state.kind === "ready" && state.tickets.length > 0 && (
          <div className="ticket-list">
            <div className="list-head">
              <span>Ref</span>
              <span>Title</span>
              <span className="category">Category</span>
              <span>Priority</span>
              <span className="status">Status</span>
              <span className="assigned-to">Assigned to</span>
              <span className="reports-to">Reports to</span>
              <span className="reasoning">Reasoning</span>
              <span className="updated">Updated</span>
            </div>
            {state.tickets.map((t) => (
              <Link
                key={t.ticket_ref}
                href={`/tickets/${encodeURIComponent(t.ticket_ref)}`}
                className="ticket-row"
              >
                <span className="ref">{t.ticket_ref}</span>
                <span className="title">{t.title}</span>
                <span className="category">{t.category}</span>
                <PriorityBadge priority={t.priority} />
                <StatusBadge status={t.status} />
                <span className="assigned-to">{t.assigned_to ?? "Unassigned"}</span>
                <span className="reports-to">{t.reports_to ?? "—"}</span>
                <span className="reasoning" title={t.reasoning ?? undefined}>
                  {t.reasoning ?? "—"}
                </span>
                <span className="updated">{relativeTime(t.updated_at)}</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
