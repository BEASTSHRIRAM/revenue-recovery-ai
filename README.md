# Revenue Recovery AI

An AI agent that recovers failed subscription payments.

Between 5% and 10% of recurring charges fail every billing cycle, and most of those failures are
*involuntary* — insufficient funds, an expired card, an issuer soft-decline — not a customer who
actually wants to leave. The standard response is a fixed retry ladder plus a generic "your payment
failed" email, which leaves most of the recoverable revenue on the table.

This platform hands each failed payment to an agent that decides what to actually do about it:

| Step | What happens |
|---|---|
| **Triage** | Reads the raw gateway decline code and classifies *why* the charge failed |
| **Score** | Predicts how recoverable this specific customer's payment is |
| **Strategy** | Picks retry timing and outreach channels to match the failure class |
| **Compose** | Writes the customer-facing message itself, tuned to tenure and amount |
| **Guardrail** | Deterministically verifies every number and claim before anything sends |
| **Learn** | Feeds the outcome back into the playbook win rates |

The insight the whole thing is built around: **the right recovery action depends entirely on why the
payment failed.** Retrying an expired card is wasted; it needs outreach. Insufficient funds needs
payday-aligned retry timing, not a retry in one hour. A hard decline needs to stop burning attempts
and escalate. One retry ladder for all of them is why conventional dunning underperforms.

## Stack

- **Frontend** — Next.js 15 (App Router, TypeScript), Tailwind, Recharts
- **Backend** — FastAPI, Pydantic v2, SQLAlchemy 2 (async)
- **Agent** — LangGraph, orchestrating **Groq** (`openai/gpt-oss-120b`) via `langchain-groq`
- **Payments** — Razorpay adapter behind a provider interface, plus a mock driver
- **Data** — SQLite out of the box, one env var away from Postgres

## Quick start

```bash
cp .env.example .env          # works as-is; add GROQ_API_KEY for the real agent

# Backend
cd backend
python -m venv .venv && .venv/Scripts/activate    # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
python -m app.db.seed                              # realistic demo data
uvicorn app.main:app --reload --port 8000

# Frontend (second terminal)
cd frontend
npm install
npm run dev                                        # http://localhost:3000
```

No keys required to see it work: the mock payment provider and seeded data drive the full flow, and
the agent falls back to a deterministic stub when `GROQ_API_KEY` is absent. Add the Groq key to get
real triage, scoring, and generated copy.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — services, data flow, request paths
- [`docs/AGENT.md`](docs/AGENT.md) — the LangGraph graph, node by node, and why each node exists
- [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) — entities and their relationships

## Status

Under active construction. See the commit history for progress.
