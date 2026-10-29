# hackFront India 2026 — build plan (FORTEC)

## Timeline

- 29 Oct 2026: project + repo started; **T1.1 picked by Ronit** (T1.2
  dropped); core graph + QA engine built first; target repo pick pending.
- 30 Oct 2026: MST submission (noon) + AgentX deck (11:59 PM) run alongside.
- 31 Oct 2026, 11:59 PM IST: prototype submission deadline (DRILL form).
- 21–22 Nov 2026: National Finale, IIIT Delhi (top 200 only).

## Build plan — T1.1 (recommended)

1. Target repo: **django/django** (picked 2026-10-29). Ingestion scope:
   recent main-branch commits + recent issues + recent PRs, linked by
   `#NNN` references; file details for the most-connected commits.
   Design docs (Django Enhancement Proposals, django/deps repo) are the
   phase-2 enrichment.
2. Ingestion: commits, PRs, issues, design docs -> entity graph
   (code entities linked to decisions, people, incidents).
3. QA: natural-language "why" questions -> evidence chain + confidence
   score + supersession/override detection + refusal when evidence is absent.
4. End-to-end tests: ingestion on a real repo, QA answers verified against
   known history, refusal case, override case.
5. Partner track: Neo4j (graph store) where it genuinely fits the build.

## Build plan — T1.2

1. Pick target real app (not built by this team).
2. Harness: device tier, intermittent network, storage/thermal/memory
   pressure, battery saver.
3. Detection + ranking by defended user-impact estimate + reproduction
   recipe per finding.
4. End-to-end tests: harness reproduces at least one real failure the
   app's team did not know about.
5. No model required; judges reward a real failure in a real app.

## Submission package (DRILL form, from the official guidance email)

1. Select Type: "Problem Selection" (or "Track Selection" for a partner track).
2. Your Problem Statement (text).
3. Prototype PPT: pdf/pptx, max 25 MB (idea, solution, features, stack,
   impact + reasoning behind design choices).
4. Source Code: zip/rar/7z, max 50 MB (must match the GitHub repo).
5. Video of Prototype (optional but expected): mp4/mov, max 25 MB,
   real features working.
6. GitHub Repository URL (public) — this repo.
7. Any Instructions (text): setup notes, demo credentials if any, AI tools
   and open-source disclosures.

Before submitting: repo is public, files within size limits, ZIP matches
GitHub, dashboard shows "Submitted". Pre-submit checkpoint with Ronit
first — no exceptions.

## Submission package status (2026-10-29)
- PPT: docs/whycode-pitch-deck.pptx — 9 slides, 38 KB, built from verified graph facts.
- Video: docs/video/whycode-demo-video.mp4 — 38 s, 990 KB, terminal screens
  (Q1 0.99, Q2 0.86, refusal) + Fish Audio narration + captions.
  Verified: narration lands in each section (silence analysis), frame readable.
- Source ZIP: docs/video/whycode-source.zip — 203 KB (whycode, tests, data,
  README, plan, demo-qa). Matches the public repo.
- **DECK PICK (Ronit, 2026-10-29): impress.js.** Submission file:
  docs/impress-deck/whycode-impress.pdf — 9 pages, 578 KB, built from the 9
  rendered step frames (1280x800). The live animated deck stays in the repo at
  docs/impress-deck/index.html and is linked in Any Instructions. Known caveat:
  the closing zoom-out frame is busy (whole map behind the text) — simplify only
  on his word.
- Field texts: docs/submission-text.md (problem statement + Any Instructions).
- Remaining: pre-submit checkpoint (Ronit's go-ahead), then DRILL upload.

## Size rule (standing)

Never build a toy or small entry. Bigger, advanced code with end-to-end
tests — the goal is top placement, not a merely valid entry.
