"use client";

import { useState } from "react";
import styles from "./page.module.css";

type RouteResult = {
  category: string;
  priority: "High" | "Medium" | "Low";
  team: string;
  reasoning: string;
  used_fallback: boolean;
  attempts_tried: number;
  latency_ms: number;
};

type RoutedTicket = {
  ticket: string;
  result: RouteResult;
};

const SAMPLES = [
  {
    label: "Angry billing",
    text: "This is RIDICULOUS. I cancelled my plan three months ago and you are STILL charging me. Fix this NOW or I'm disputing every charge with my bank.",
  },
  {
    label: "Outage",
    text: "Every API call from our production system has been returning 503 for the last 20 minutes. Nothing on your status page.",
  },
  { label: "Vague", text: "it doesn't work" },
  {
    label: "SDK how-to",
    text: "How do I paginate through results when calling the /v1/list-runs endpoint from the Python SDK?",
  },
];

function ResultCard({
  item,
  showTicket,
}: {
  item: RoutedTicket;
  showTicket: boolean;
}) {
  const { ticket, result } = item;
  return (
    <div className={styles.card}>
      <div className={styles.result}>
        {showTicket && <div className={styles.ticketText}>{ticket}</div>}
        {result.used_fallback && (
          <div className={styles.fallbackNote}>
            Automatic classification failed — this ticket was flagged for
            human review.
          </div>
        )}
        <div className={styles.team}>
          <small>Routed to</small>
          {result.team}
        </div>
        <div className={styles.badges}>
          <span className={`${styles.pill} ${styles.category}`}>
            {result.category}
          </span>
          <span className={`${styles.pill} ${styles[result.priority]}`}>
            {result.priority} priority
          </span>
        </div>
        <div className={styles.reasoning}>{result.reasoning}</div>
        <div className={styles.meta}>
          {result.latency_ms.toFixed(0)} ms · {result.attempts_tried} attempt
          {result.attempts_tried > 1 ? "s" : ""}
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const [ticket, setTicket] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latest, setLatest] = useState<RoutedTicket | null>(null);
  const [history, setHistory] = useState<RoutedTicket[]>([]);

  async function route() {
    const text = ticket.trim();
    if (!text || loading) return;

    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/classify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticket: text }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        const msg =
          detail?.detail?.[0]?.msg ??
          (typeof detail?.detail === "string" ? detail.detail : null) ??
          `Request failed (${res.status})`;
        throw new Error(msg);
      }
      const result: RouteResult = await res.json();
      if (latest) setHistory((h) => [latest, ...h]);
      setLatest({ ticket: text, result });
      setTicket("");
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(
        msg === "Failed to fetch"
          ? "Could not reach the router API — is the backend running?"
          : msg,
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.wrap}>
      <header className={styles.header}>
        <h1>Smart Ticket Router</h1>
        <p>
          Paste a support ticket — get the category, priority, and owning team
          back as structured output.
        </p>
      </header>

      <div className={styles.card}>
        <textarea
          className={styles.textarea}
          value={ticket}
          onChange={(e) => setTicket(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") route();
          }}
          placeholder="e.g. I've been charged twice for my Pro subscription this month…"
        />
        <div className={styles.controls}>
          <div className={styles.samples}>
            {SAMPLES.map((s) => (
              <button key={s.label} onClick={() => setTicket(s.text)}>
                {s.label}
              </button>
            ))}
          </div>
          <button
            className={styles.submit}
            onClick={route}
            disabled={loading || !ticket.trim()}
          >
            {loading ? "Routing…" : "Route ticket"}
          </button>
        </div>
        <div className={styles.hint}>Tip: Cmd/Ctrl + Enter submits.</div>
      </div>

      {error && <div className={styles.error}>{error}</div>}
      {latest && <ResultCard item={latest} showTicket={false} />}

      {history.length > 0 && (
        <section>
          <h2 className={styles.historyHeading}>Previously routed</h2>
          {history.map((item, i) => (
            <ResultCard key={history.length - i} item={item} showTicket />
          ))}
        </section>
      )}
    </div>
  );
}
