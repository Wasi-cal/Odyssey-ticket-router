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
      <div className="page-header">
        <h1 className="page-title">My tickets</h1>
        {state.kind === "ready" && state.tickets.length > 0 && (
          <span className="ticket-count">
            Total: <strong>{state.tickets.length}</strong>
          </span>
        )}
      </div>

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
          <div className="ticket-table-wrapper">
            <div className="ticket-list">
              <div className="list-head">
                <span className="ref">Ref</span>
                <span className="title">Title</span>
                <span className="category">Category</span>
                <span className="priority">Priority</span>
                <span className="status">Status</span>
                <span className="assigned-to">Assigned to</span>
                <span className="reports-to">Reports to</span>
                <span className="updated">Updated</span>
              </div>
              
              <div className="list-body">
                {state.tickets.map((t) => (
                  <Link
                    key={t.ticket_ref}
                    href={`/tickets/${encodeURIComponent(t.ticket_ref)}`}
                    className="ticket-row"
                  >
                    <span className="ref">{t.ticket_ref}</span>
                    <span className="title" title={t.title}>{t.title}</span>
                    <span className="category">{t.category}</span>
                    <span className="priority">
                      <PriorityBadge priority={t.priority} />
                    </span>
                    <span className="status">
                      <StatusBadge status={t.status} />
                    </span>
                    <span className="assigned-to">{t.assigned_to ?? "Unassigned"}</span>
                    <span className="reports-to">{t.reports_to ?? "—"}</span>
                    <span className="updated">{relativeTime(t.updated_at)}</span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}