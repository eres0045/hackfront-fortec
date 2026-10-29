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

## Size rule (standing)

Never build a toy or small entry. Bigger, advanced code with end-to-end
tests — the goal is top placement, not a merely valid entry.
