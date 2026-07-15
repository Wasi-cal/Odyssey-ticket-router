// Jira-style lozenges for priority and status. Unknown values fall back to
// a neutral badge rather than breaking, since status values will firm up
// as the backend evolves.

const PRIORITY_TONE: Record<string, string> = {
  high: "danger",
  medium: "warn",
  low: "neutral",
};

const STATUS_TONE: Record<string, string> = {
  open: "info",
  "to do": "info",
  new: "info",
  "in progress": "info",
  pending: "warn",
  "on hold": "warn",
  blocked: "danger",
  resolved: "ok",
  done: "ok",
  closed: "neutral",
};

export function PriorityBadge({ priority }: { priority: string }) {
  const tone = PRIORITY_TONE[priority.toLowerCase()] ?? "neutral";
  return <span className={`badge ${tone}`}>{priority}</span>;
}

export function StatusBadge({ status }: { status: string }) {
  const tone = STATUS_TONE[status.toLowerCase()] ?? "neutral";
  return <span className={`badge ${tone} status-badge`}>{status}</span>;
}
