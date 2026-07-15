"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { AuthError, fetchTicket, type TicketDetail } from "../../../lib/api";
import { relativeTime, absoluteTime } from "../../../lib/format";
import { PriorityBadge, StatusBadge } from "../../../components/Badge";

type State =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; ticket: TicketDetail };

export default function TicketDetailPage() {
  const params = useParams<{ ticket_ref: string }>();
  const ticketRef = decodeURIComponent(params.ticket_ref);
  const router = useRouter();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    fetchTicket(ticketRef)
      .then((ticket) => setState({ kind: "ready", ticket }))
      .catch((err) => {
        if (err instanceof AuthError) {
          router.replace("/login");
          return;
        }
        setState({
          kind: "error",
          message: err instanceof Error ? err.message : "Failed to load ticket.",
        });
      });
  }, [ticketRef, router]);

  if (state.kind === "loading") {
    return (
      <main className="page">
        <div className="card">
          <div className="state">Loading {ticketRef}…</div>
        </div>
      </main>
    );
  }

  if (state.kind === "error") {
    return (
      <main className="page">
        <div className="card">
          <div className="state">
            <div className="error-box">{state.message}</div>
          </div>
        </div>
      </main>
    );
  }

  const t = state.ticket;

  return (
    <main className="page">
      <div className="detail-header">
        <span className="crumb">
          <Link href="/tickets">My tickets</Link> /
        </span>
        <span className="ref">{t.ticket_ref}</span>
        <span className="crumb">{t.category}</span>
      </div>

      <div className="detail-grid">
        <div className="card detail-main">
          <h1>{t.title}</h1>
          <p className="description">{t.description || "No description."}</p>
          {t.reasoning && (
            <div className="reasoning">
              <span className="label">Why this routing?</span>
              {t.reasoning}
            </div>
          )}
        </div>

        <dl className="card detail-side">
          <div className="row">
            <dt>Team</dt>
            <dd>{t.team ?? "—"}</dd>
          </div>
          <div className="row">
            <dt>Assigned to</dt>
            <dd>{t.assigned_to ?? "Unassigned"}</dd>
          </div>
          <div className="row">
            <dt>Role</dt>
            <dd>{t.role ?? "—"}</dd>
          </div>
          <div className="row">
            <dt>Reports to</dt>
            <dd>{t.reports_to ?? "—"}</dd>
          </div>
          <div className="row">
            <dt>Estimated time</dt>
            <dd>{t.estimated_time ?? "—"}</dd>
          </div>
          <div className="row">
            <dt>Priority</dt>
            <dd>
              <PriorityBadge priority={t.priority} />
            </dd>
          </div>
          <div className="row">
            <dt>Status</dt>
            <dd>
              <StatusBadge status={t.status} />
            </dd>
          </div>
          <div className="row">
            <dt>Last updated</dt>
            <dd title={absoluteTime(t.updated_at)}>
              {relativeTime(t.updated_at)}
            </dd>
          </div>
        </dl>
      </div>
    </main>
  );
}
