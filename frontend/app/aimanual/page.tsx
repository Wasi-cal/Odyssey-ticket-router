"use client";

// AI vs. manual: runs the 20 demo tickets from /compare_tickets.json through
// the live classifier (POST /classify — never persists) while a human routes
// the same tickets by hand via the dropdowns below. Nothing on this page
// touches the ticket database; it's purely a live agreement check between
// the model and a manual reviewer.

import { useEffect, useRef, useState } from "react";
import { classifyTicket, type ClassifyResult } from "../../lib/api";
import { ROSTER, MANAGER_NAMES, reportsToFor } from "../../lib/roster";

type Category = { id: string; label: string; team: string };

type AiState =
  | { status: "idle" }
  | { status: "running" }
  | { status: "done"; result: ClassifyResult; latencyMs: number }
  | { status: "error"; message: string };

type ManualState = {
  category: string;
  priority: string;
  assignedTo: string;
  reportsTo: string;
};

const CONCURRENCY = 4;

function pad(n: number): string {
  return String(n).padStart(3, "0");
}

function truncate(text: string, length: number): string {
  return text.length > length ? `${text.slice(0, length)}…` : text;
}

export default function AiVsManualPage() {
  const [tickets, setTickets] = useState<string[] | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [priorities, setPriorities] = useState<string[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [aiStates, setAiStates] = useState<AiState[]>([]);
  const [manual, setManual] = useState<ManualState[]>([]);
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const [runStart, setRunStart] = useState<number | null>(null);
  const [runEnd, setRunEnd] = useState<number | null>(null);
  const logRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("/compare_tickets.json").then((r) => r.json()),
      fetch("/taxonomy.json").then((r) => r.json()),
    ])
      .then(([ticketList, taxonomy]: [string[], { categories: Category[]; priorities: string[] }]) => {
        setTickets(ticketList);
        setCategories(taxonomy.categories);
        setPriorities(taxonomy.priorities);
        setAiStates(ticketList.map(() => ({ status: "idle" })));
        setManual(
          ticketList.map(() => ({ category: "", priority: "", assignedTo: "", reportsTo: "" })),
        );
      })
      .catch((err) =>
        setLoadError(err instanceof Error ? err.message : "Failed to load demo data."),
      );
  }, []);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [log]);

  async function runAll() {
    if (!tickets || running) return;
    setRunning(true);
    setLog([]);
    setRunStart(performance.now());
    setRunEnd(null);
    setAiStates(tickets.map(() => ({ status: "idle" })));

    const total = tickets.length;
    let cursor = 0;
    const appendLog = (line: string) => setLog((prev) => [...prev, line]);

    async function worker() {
      while (cursor < total) {
        const i = cursor++;
        const text = tickets![i];
        setAiStates((prev) => {
          const next = [...prev];
          next[i] = { status: "running" };
          return next;
        });
        appendLog(`[${i + 1}/${total}] classifying "${truncate(text, 70)}"`);

        const start = performance.now();
        try {
          const result = await classifyTicket(text);
          const latencyMs = performance.now() - start;
          setAiStates((prev) => {
            const next = [...prev];
            next[i] = { status: "done", result, latencyMs };
            return next;
          });
          appendLog(
            `[${i + 1}/${total}] done -> ${result.category} / ${result.priority} (${Math.round(latencyMs)}ms)`,
          );
        } catch (err) {
          const message = err instanceof Error ? err.message : "classification failed";
          setAiStates((prev) => {
            const next = [...prev];
            next[i] = { status: "error", message };
            return next;
          });
          appendLog(`[${i + 1}/${total}] error -> ${message}`);
        }
      }
    }

    await Promise.all(Array.from({ length: Math.min(CONCURRENCY, total) }, worker));
    setRunEnd(performance.now());
    setRunning(false);
  }

  function updateManual(i: number, patch: Partial<ManualState>) {
    setManual((prev) => {
      const next = [...prev];
      next[i] = { ...next[i], ...patch };
      return next;
    });
  }

  if (loadError) {
    return (
      <main className="page">
        <h1 className="page-title">AI vs. Manual</h1>
        <div className="card">
          <div className="state">
            <div className="error-box">{loadError}</div>
          </div>
        </div>
      </main>
    );
  }

  if (!tickets) {
    return (
      <main className="page">
        <h1 className="page-title">AI vs. Manual</h1>
        <div className="card">
          <div className="state">Loading demo tickets…</div>
        </div>
      </main>
    );
  }

  const doneCount = aiStates.filter((s) => s.status === "done" || s.status === "error").length;
  const latencies = aiStates
    .filter((s): s is Extract<AiState, { status: "done" }> => s.status === "done")
    .map((s) => s.latencyMs);
  const avgLatency = latencies.length ? latencies.reduce((a, b) => a + b, 0) / latencies.length : 0;
  const totalElapsed = runStart != null ? (runEnd ?? performance.now()) - runStart : null;

  return (
    <main className="page">
      <h1 className="page-title">AI vs. Manual</h1>
      <p className="page-subtitle">
        Run the same 20 demo tickets through the live classifier, then route them yourself by
        hand below. Nothing here writes to the database — it&apos;s just a live look at where the
        model and a manual reviewer agree or disagree, and how fast each gets there.
      </p>

      <section className="card av-section">
        <div className="av-section-head">
          <h2>Live AI classification</h2>
          <button className="btn-primary" onClick={runAll} disabled={running}>
            {running ? "Classifying…" : doneCount > 0 ? "Run again" : "Run AI classification"}
          </button>
        </div>

        <div className="av-stats">
          <div>
            <span className="av-stat-value">
              {doneCount}/{tickets.length}
            </span>
            <span className="av-stat-label">completed</span>
          </div>
          <div>
            <span className="av-stat-value">{avgLatency ? `${Math.round(avgLatency)}ms` : "—"}</span>
            <span className="av-stat-label">avg latency</span>
          </div>
          <div>
            <span className="av-stat-value">
              {totalElapsed != null ? `${(totalElapsed / 1000).toFixed(1)}s` : "—"}
            </span>
            <span className="av-stat-label">total run time</span>
          </div>
        </div>

        <div className="av-log" ref={logRef}>
          {log.length === 0 && (
            <div className="av-log-empty">Run the classifier to see live output here.</div>
          )}
          {log.map((line, i) => (
            <div key={i} className="av-log-line">
              {line}
            </div>
          ))}
        </div>

        <div className="av-feed-grid">
          {tickets.map((text, i) => (
            <AiFeedItem key={i} text={text} state={aiStates[i]} />
          ))}
        </div>
      </section>

      <section className="card av-section">
        <div className="av-section-head">
          <h2>Manual routing</h2>
        </div>
        <p className="page-subtitle" style={{ marginBottom: 16 }}>
          Pick a category, priority, assignee and manager for each ticket — same fields the AI
          decides, filled in by hand.
        </p>

        <div className="manual-grid">
          {tickets.map((text, i) => (
            <ManualCard
              key={i}
              ticketNo={`CMP-${pad(i + 1)}`}
              text={text}
              categories={categories}
              priorities={priorities}
              value={manual[i]}
              onChange={(patch) => updateManual(i, patch)}
            />
          ))}
        </div>
      </section>

      <section className="card av-section">
        <h2>Side-by-side comparison</h2>
        <CompareTable tickets={tickets} aiStates={aiStates} manual={manual} />
      </section>
    </main>
  );
}

function AiFeedItem({ text, state }: { text: string; state: AiState }) {
  const dotClass =
    state.status === "running" ? "running" : state.status === "done" ? "done" : state.status === "error" ? "error" : "";

  return (
    <div className="av-feed-item">
      <span className={`av-dot ${dotClass}`} />
      <div style={{ minWidth: 0, flex: 1 }}>
        <div className="av-feed-text" title={text}>
          {truncate(text, 60)}
        </div>
        {state.status === "done" && (
          <div className="av-feed-result">
            <span className="badge info">{state.result.category}</span>
            <span className="badge neutral">{state.result.priority}</span>
            <span className="av-feed-ms">{Math.round(state.latencyMs)}ms</span>
          </div>
        )}
        {state.status === "error" && <div className="av-feed-result badge danger">{state.message}</div>}
        {state.status === "running" && <div className="av-feed-result badge info">classifying…</div>}
      </div>
    </div>
  );
}

function ManualCard({
  ticketNo,
  text,
  categories,
  priorities,
  value,
  onChange,
}: {
  ticketNo: string;
  text: string;
  categories: Category[];
  priorities: string[];
  value: ManualState;
  onChange: (patch: Partial<ManualState>) => void;
}) {
  return (
    <div className="manual-card">
      <div className="manual-card-head">
        <span className="manual-card-ref">{ticketNo}</span>
      </div>
      <div className="manual-card-text">{text}</div>

      <div className="manual-card-fields">
        <div>
          <label htmlFor={`${ticketNo}-category`}>Category</label>
          <select
            id={`${ticketNo}-category`}
            value={value.category}
            onChange={(e) => onChange({ category: e.target.value })}
          >
            <option value="">Select…</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor={`${ticketNo}-priority`}>Priority</label>
          <select
            id={`${ticketNo}-priority`}
            value={value.priority}
            onChange={(e) => onChange({ priority: e.target.value })}
          >
            <option value="">Select…</option>
            {priorities.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor={`${ticketNo}-assigned`}>Assigned to</label>
          <select
            id={`${ticketNo}-assigned`}
            value={value.assignedTo}
            onChange={(e) =>
              onChange({ assignedTo: e.target.value, reportsTo: reportsToFor(e.target.value) })
            }
          >
            <option value="">Select…</option>
            {ROSTER.map((r) => (
              <option key={r.name} value={r.name}>
                {r.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor={`${ticketNo}-reports`}>Reports to</label>
          <select
            id={`${ticketNo}-reports`}
            value={value.reportsTo}
            onChange={(e) => onChange({ reportsTo: e.target.value })}
          >
            <option value="">Select…</option>
            {MANAGER_NAMES.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

function CompareTable({
  tickets,
  aiStates,
  manual,
}: {
  tickets: string[];
  aiStates: AiState[];
  manual: ManualState[];
}) {
  let categoryAgree = 0;
  let priorityAgree = 0;
  let comparable = 0;

  const rows = tickets.map((text, i) => {
    const ai = aiStates[i];
    const man = manual[i];
    const aiDone = ai.status === "done" ? ai : null;
    const hasBoth = !!aiDone && !!man.category && !!man.priority;
    if (hasBoth) {
      comparable++;
      if (aiDone!.result.category === man.category) categoryAgree++;
      if (aiDone!.result.priority === man.priority) priorityAgree++;
    }
    return { text, ai, man, hasBoth, aiDone };
  });

  return (
    <>
      <div className="compare-summary">
        <div>
          <span className="av-stat-value">
            {comparable > 0 ? `${categoryAgree}/${comparable}` : "—"}
          </span>
          <span className="av-stat-label">category agreement</span>
        </div>
        <div>
          <span className="av-stat-value">
            {comparable > 0 ? `${priorityAgree}/${comparable}` : "—"}
          </span>
          <span className="av-stat-label">priority agreement</span>
        </div>
        <div>
          <span className="av-stat-value">
            {comparable}/{tickets.length}
          </span>
          <span className="av-stat-label">tickets with both sides filled in</span>
        </div>
      </div>

      <div className="compare-table-wrap">
        <table className="compare-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Ticket</th>
              <th>AI category</th>
              <th>Manual category</th>
              <th>Match</th>
              <th>AI priority</th>
              <th>Manual priority</th>
              <th>Match</th>
              <th>AI time</th>
              <th>Assigned to</th>
              <th>Reports to</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              const categoryMatch = row.hasBoth
                ? row.aiDone!.result.category === row.man.category
                : null;
              const priorityMatch = row.hasBoth
                ? row.aiDone!.result.priority === row.man.priority
                : null;
              return (
                <tr key={i}>
                  <td>{pad(i + 1)}</td>
                  <td className="cmp-text">{truncate(row.text, 90)}</td>
                  <td>{row.aiDone ? row.aiDone.result.category : row.ai.status === "error" ? "error" : "—"}</td>
                  <td>{row.man.category || "—"}</td>
                  <td>
                    <span
                      className={`cmp-match ${categoryMatch === null ? "pending" : categoryMatch ? "yes" : "no"}`}
                    >
                      {categoryMatch === null ? "…" : categoryMatch ? "✓" : "✗"}
                    </span>
                  </td>
                  <td>{row.aiDone ? row.aiDone.result.priority : row.ai.status === "error" ? "error" : "—"}</td>
                  <td>{row.man.priority || "—"}</td>
                  <td>
                    <span
                      className={`cmp-match ${priorityMatch === null ? "pending" : priorityMatch ? "yes" : "no"}`}
                    >
                      {priorityMatch === null ? "…" : priorityMatch ? "✓" : "✗"}
                    </span>
                  </td>
                  <td>{row.aiDone ? `${Math.round(row.aiDone.latencyMs)}ms` : "—"}</td>
                  <td>{row.man.assignedTo || "—"}</td>
                  <td>{row.man.reportsTo || "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
