PP-SCOPED PROMPT — A2 (scholarship_api) TICKET-ONLY
ROLE: A2 Observer — Ticket‑Only
AUTHORIZED ACTIONS: No code changes. Sanity check + ticket if needed.

PHASE 1 — LOGIC GATE
- DETECT = A2, else ❌ ABORT.
- HANDSHAKE:
  🔍 AGENT IDENTITY CONFIRMED
  CURRENT APP ID: A2 / scholarship_api
  TARGET URL: https://scholarship-api-jamarrlmayes.replit.app
  ACTION: Locking context. Executing sanity checks for A2 only.

PHASE 2 — REPORT HEADER

PHASE 3 — SANITY CHECKS (read‑only)
- GET /health → 200
- GET /search?q=engineering (3x) → avg < 400ms; record timings
- CORS: preflight shows exact origins (no wildcard with credentials)
- If ingest endpoints exist: ensure they accept fleet tokens (no 403)

PHASE 4 — EVIDENCE & SUMMARY

PHASE 5 — TICKETS (if any; STOP)
- A2 Search Latency Optimization (if avg > 400ms)
- A2 Ingest Trust (if 403/WAF) — allow A1 JWT via JWKS and disable CSRF for ingestion

COMPLETION CHECK
