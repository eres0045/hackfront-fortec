# hackFront Finale Timeline — WhyCode / Team FORTEC
# Sat 21 Nov 14:00 → Sun 22 Nov 15:30, IIIT Delhi

## SATURDAY 21 NOV
- **14:51 → 16:00 — Build Plan (due 4 PM, submission gate).** First-user name from Ronit → Muse fills it into the one-page plan PDF → Ronit submits before 16:00.
- **15:00–18:00 — Build block 1.** Muse: Flask UI (ask → answer card with confidence + best match + superseded banner → clickable evidence chain → graph view) against the current qa.py interface. Ronit: Neo4j AuraDB Free mirror + Cypher chain serving. Udita: Market Fit Canvas draft (target customer, payer $20/user/month hypothesis, first-100-users plan).
- **17:00 tea / 18:00 speaker session** — keep building; speaker session is a breather if needed.
- **18:00–19:00 — Deploy.** UI live on Render (public URL). Neo4j mirror working. Evaluator-alone test from a phone.
- **19:00–20:00 — 3 customer interviews** (10 min each, call/video/in person — Django newcomers / GSoC aspirants; mentors count only if in segment). Record assumed / found / changed for each. Finish the Market Fit Canvas from what they said.
- **20:00–21:00 — MENTOR ROUND 1 (scored).** Present plan vs progress. One revision of the plan allowed here with mentor sign-off, then locked. Dinner 20:30–21:30 overlaps.
- **21:00–23:30 — Build block 2.** Integrate Neo4j chain serving into the UI. Supersedes edges (DEP "Superseded by" + "Reverts" commits) + banner. BM25 ranking (title 2×). Chain cleanup (no authored expansion on hop 2, match entity out of its own chain). Second segment live (maintainers: supersedes banner = their journey).
- **23:30–23:45 — ArgosX BASELINE scan** on the live URL (Deep scan, getargosx.com, no account, under 2 min) → download report. Midnight deadline.
- **23:30–00:15 — Prompt Battle** (optional — skip if behind).
- **00:00 — Baseline report saved** (submission-gate item 1 of 2).

## SUNDAY 22 NOV
- **00:15–02:00 — Overnight, fixes only.** Fix ArgosX critical/high findings. Persona Use Case Matrix (3 segments × 2 use cases). Freeze new features after this.
- **02:00–06:00 — Rest in shifts** (one rests 02:00–04:00, the other 04:00–06:00). Fixes only, no new features.
- **07:00–09:00 — Checkpoint + breakfast.** Verify everything: live URL, Neo4j chains, supersedes banner, BM25, clean chains. Rehearse the demo (CLI yesterday → live product today, 2-minute story).
- **09:00–09:30 — ArgosX FINAL scan** → download report → write the remediation log (found / fixed / remains + why). Submit both reports + log by 11:00.
- **09:30–10:00 — Final demo dry run** (fresh browser, ask Q1, check the chain, check the refusal Q2).
- **10:00–11:00 — MENTOR ROUND 2 (scored — the judgement round; Top 12 effectively picked here).** Demo-ready by 10:00.
- **11:00–12:00 — ArgosX final report submitted (by 11:00).** Prep the jury demo.
- **12:00–12:10 — CODE FREEZE.** No new code after 12:00.
- **12:15–12:30 — Top 12 announced.**
- **12:30–14:30 — Jury demos** (if in Top 12).
- **14:30–15:30 — Closing.**
- **After — Hotel for Sun night + return travel** (still unbooked — sort during a break, e.g. dinner or the speaker session).

## COORDINATION
- **Interface contract:** UI reads the answer object from qa.py (answer, confidence, best match, chain records, superseded flag). Neo4j swaps how the chain is fetched, not the shape. SQLite stays the source of truth; UI falls back to SQLite if Neo4j is unreachable.
- **Split (proposed — Ronit can swap):** Muse = UI + deploy + ArgosX scans + canvas/matrix drafts. Ronit = Neo4j + supersedes + BM25 + chain cleanup + interviews. Udita = canvas + matrix + interviews + demo story.
- **Kill criteria:** if the UI isn't live by 19:00, cut the graph view and ship ask → answer → chain only. If Neo4j isn't serving chains by 23:00, demo with SQLite and show Neo4j as the mirror (honest fallback).
