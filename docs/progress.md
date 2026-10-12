# HW5 progress

| # | Problem | Status |
|---|---|---|
| 1 | Repo skeleton, data, reset script, model check | Done |
| 2 | MCP server — shop tools over the working DB | Not started |
| 3 | Agent team (Boss + 4 specialists, fully connected) | Not started |
| 4 | FastAPI backend — board, runs, approvals | Not started |
| 5 | React dashboard | Not started |
| 6 | Full reset-and-run over all three tickets | Not started |
| 7 | Push to a public GitHub repo | Not started |

*(The brief did not number the problems; this is the working breakdown and it
will be revised as the user hands over each next problem.)*

## 1 — Repo skeleton, data, reset script, model check

- Unzipped the supplied archive to `data/campus_customs.db` (53 KB, 9 tables).
- `scripts/reset_db.py` copies the seed to `data/campus_customs_new.db`,
  hashes the seed before and after to prove it was not touched, clears stale
  WAL/SHM sidecars, and prints row counts plus cash and `date_today`.
- `.gitignore` excludes `.env`, the working DB copy, `.venv/`, `output/`.
  The seed DB *is* committed — it is the assignment's input and the grader
  needs it to run anything.
- `.env.example` carries placeholders only.
- **Model verified against the live gateway:** `gpt-6-luna` resolves to
  `gpt-6-luna-2026-09-22`. A deliberately wrong name did *not* error — it
  silently answered as `gpt-5.6-luna-2026-07-09`. Hence the runtime assertion
  on `response.model` recorded in CLAUDE.md.
