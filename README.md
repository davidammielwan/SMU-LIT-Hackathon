# Amenda — regulatory change impact engine

Horizon scanning tells you the law changed. Amenda tells you **which of your
clients' documents are now wrong, why, and what to do** — with a verbatim
clause quote behind every flag.

## Run

```
cd amenda/backend
pip install fastapi uvicorn python-dotenv httpx requests beautifulsoup4
python -m uvicorn main:app --port 8000
```

Open http://127.0.0.1:8000

Create `amenda/.env` (NOT committed) with:

```
OPENROUTER_API_KEY=sk-or-...
AMENDA_MODEL=anthropic/claude-sonnet-4.5
```

## Features

1. **Horizon scanning (Feature 1)** — right panel.
   - *Confirmed* tab: gazetted amendments with before/after text and authority.
   - *Watchlist* tab: bills scraped **live from parliament.gov.sg** (with a
     cached-snapshot fallback), merged with Hansard-derived minister
     commencement signals: `imminent` / `~1 year` / **`not stated`** (the tool
     says explicitly when the Minister has given no commencement signal).
   - PAIR Search / eGazette / SSO are JS apps or bot-blocked (verified):
     served from fixtures behind the same parser interface; headless-browser
     fetch is the production path.
2. **Impact sweep (Feature 2)** — select amendments, press send. One LLM call
   per (amendment, client); each document is classified
   `high` (Highest priority) / `moderate` (Moderate risk) / `unaffected`.
   - Topical overlap is NOT impact: a PDPA consent form is not flagged by a
     PDPA breach-window change. The corpus contains deliberate traps to prove it.
   - Every flag carries a **verbatim clause quote** and a confidence marker:
     `found` (quote states the outdated position) vs `inferred`.
   - **Profile matches**: exposure the firm knows from the client profile even
     when no document shows it (e.g. headcount ≥ 25 → Workplace Fairness).
3. **Evaluation** — `python backend/eval.py` scores the sweep against
   hand-labelled ground truth (`data/ground_truth.json`): precision, recall,
   and false-positive traps passed.

## Architecture

```
backend/
  main.py               FastAPI — API + serves frontend
  llm.py                OpenRouter client (.env)
  analysis/impact.py    sweep engine: per-(amendment, client) verdicts
  scrapers/parliament.py live scrape of Bills Introduced + fixture fallback
  data/                 amendments, watchlist, clients (synthetic), ground truth
  eval.py               precision/recall vs ground truth
frontend/
  index.html            Vue 3 (CDN, no build step) + Classical design system
```

Client corpus is **synthetic** (no real client data); regulatory sources are
real. The engine is domain-agnostic — the demo goes deep on PDPA/Employment.
