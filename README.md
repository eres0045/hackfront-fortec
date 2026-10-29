# FORTEC — hackFront India 2026 Prototype

Team FORTEC (Ronit Shrimankar — lead, Anshul Kamthe, Udita Singh).
Theme: AI and Developer Tools (T-1). Registration complete ("Team Ready").

## Event

- Prototype submission deadline: **31 October 2026, 11:59 PM IST**
- National Finale (top 200 teams): **21–22 November 2026, IIIT Delhi** (24-hour, in person)
- Prize pool: ₹3.5 lakh + partner tracks (Neo4j, Sarvam, Arduino)

## Problem: T1.1 — Why The Code Is Like This (picked 2026-10-29)

Ingest a public repo's commits, PRs, issues and design docs into a graph;
answer "why" questions with a cited evidence chain, supersession/override
detection and a confidence score; refuse to invent answers not in the
graph. Target public repo: pending Ronit's pick (shortlist in
`docs/plan.md`). T1.2 dropped.

## Setup

```text
python3 -m whycode.cli --db data/whycode.db --question "Why ...?"
```

The bundled `data/whycode.db` holds the demo graph (200 Django commits,
100 PRs, 100 Trac tickets), so the demo runs with no API calls and no
credentials. To rebuild it from scratch:

```text
python3 -m whycode.ingest --repo django/django --db data/whycode.db
python3 -m whycode.trac --db data/whycode.db --limit 100
```

Run the tests with `python3 -m unittest discover -s tests`.

## Judging (from the official criteria)

1. Problem/Track Alignment
2. Innovation & Solution Effectiveness
3. Technical Implementation & Code Quality
4. Functionality & Prototype Validation
5. Critical Thinking & Practical Implementation

Official tip: half the score comes from technical implementation and a
working prototype. The demo video must show real features working, not
slides. The PPT must explain the reasoning behind design choices.

## Submission checklist

See `docs/plan.md`. No submission without Ronit's pre-submit checkpoint.
