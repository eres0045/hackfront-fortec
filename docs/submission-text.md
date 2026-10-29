# DRILL submission field texts — WhyCode (FORTEC, T-1)

## Form: Selected Format = AI and Developer Tools
## Form: Select Type = Problem Selection

## Your Problem Statement

Developers constantly ask "why is this code like this?" and cannot get a trustworthy
answer. The reasons behind code live scattered across commits, pull requests, and
issue trackers — never linked to the code they explain — so new developers guess,
and wrong guesses break things the original author fixed on purpose.

WhyCode ingests a public repository's real history (for this prototype: django/django
— 200 commits, 100 PRs, 100 Trac tickets, 161 files, 90 people, 27 design docs
(Django Enhancement Proposals), 641 edges) into a
graph linking code entities to the decisions, people, and incidents behind them.
Design docs are included: 27 Django Enhancement Proposals ingested as doc
entities, linked by mentions edges to the files they name.
It answers plain-language "why" questions with a cited evidence chain and a
confidence score — and refuses to answer when the graph holds no evidence, instead
of inventing one. Django was chosen because it tracks decisions in Trac rather than
GitHub Issues, which proves the tool handles real-world, messy decision history.

## Github Repository URL (Public)

https://github.com/eres0045/hackfront-fortec

## Any Instructions

- Setup: clone the repo, run `python3 -m whycode.cli --db data/whycode.db
  --question "Why ...?"`. No accounts, API keys, or paid services needed — the
  bundled SQLite database runs the full demo offline.
- The submitted PPT is a flat PDF export of the impress.js deck; the live,
  animated version is in the repo at `docs/impress-deck/index.html` (open in a
  browser, arrow keys/spacebar to navigate the 3D path).
- Demo video shows the tool's real CLI output for three questions (two answers,
  one refusal).
- Open-source and tools disclosure: Python standard library, SQLite, gh CLI for
  ingestion, impress.js for the deck, Fish Audio for the demo video's narration.
  Django's history is public data. No paid APIs were used.
- Tests: `python3 -m unittest discover -s tests` — 13/13 pass, including the
  refusal and supersession cases.
