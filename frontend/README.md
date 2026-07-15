# Smart Ticket Router — frontend

Next.js UI for raising and tracking tickets. Talks only to the FastAPI
backend (no direct database or LLM access) through the `/api/*` proxy in
`next.config.ts`, so the backend needs no CORS setup.

## Pages

| Route | What it does |
|---|---|
| `/` | Raise a ticket — `POST /tickets` with `{submitted_by, text}`, then redirects to the new ticket's detail page. |
| `/tickets` | My tickets — `GET /tickets?submitted_by=X`, one dense row per ticket. |
| `/tickets/[ticket_ref]` | Ticket detail — `GET /tickets/{ticket_ref}`, description on the left, assignment/priority/status panel on the right. |

Identity is just the name/email kept in `localStorage` under `submitted_by`
(no real auth yet — planned as a JWT upgrade later).

## Expected API shapes

```jsonc
// GET /tickets?submitted_by=X  -> array of:
// GET /tickets/{ticket_ref}    -> one of (plus description/assignment fields):
{
  "ticket_ref": "SA-42",
  "title": "Duplicate charge on invoice",
  "description": "…",                // detail only
  "category": "Billing",             // human label
  "priority": "High",                // High | Medium | Low
  "status": "Open",
  "assigned_to": "Priya Sharma",     // detail only — assignee name
  "role": "Billing Specialist",      // detail only
  "reports_to": "Dan Cole",          // detail only — manager's name
  "estimated_time": "4h",            // detail only
  "updated_at": "2026-07-15T10:00:00Z"
}
```

`lib/api.ts` normalizes minor shape drift (e.g. `category_label`, a nested
`assigned_to` object) so the pages only ever see the flat shape above.

## Run

```bash
npm install
npm run dev        # http://localhost:3000, proxies /api/* to :8000
```

Set `BACKEND_URL` to point at a backend other than `http://127.0.0.1:8000`.
Note: rewrites are resolved when the server loads the config — for a
production build (`npm run build && npm start`), set `BACKEND_URL` at build
time.
