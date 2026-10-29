---
theme: default
title: WhyCode — by FORTEC
info: |
  WhyCode answers "why is this code like this?" from a repo's own history.
  hackFront India 2026, Theme: AI and Developer Tools (T-1).
---

# WhyCode

Why is this code like this? Ask its own history.

<div class="pt-12">
  <span class="text-green-400 font-bold">Team FORTEC</span> · hackFront India 2026 · AI and Developer Tools (T-1)
</div>

<div class="opacity-60 text-sm mt-4">
  Ronit Shrimankar (lead) · Anshul Kamthe · Udita Singh · built on django/django
</div>

---

# The problem

- Codebases accumulate decisions **nobody can explain any more**
- A new developer reads an odd function and **guesses** why it exists
- A wrong guess breaks something the original author fixed on purpose
- The reasons live scattered across **commits, pull requests and tickets** — never in one place, never linked to the code they explain

---

# The solution: WhyCode

Ingest a public repo's history into a **graph**, then ask it plain-language *why* questions.

- **Ingest** — commits, PRs, and tickets (Django tracks decisions in **Trac**, not GitHub Issues)
- **Graph** — code entities linked to decisions, people, and incidents
- **Ask** — get a **cited evidence chain** and a confidence score
- **Refuse** — when the graph holds no evidence, it refuses. No invented answers, ever.

---

# How it works

1. **Ingest** — GitHub API via `gh` (commits, PRs) + Trac ticket pages
2. **Graph** — entities: commit, PR, ticket, file, person · edges: authored, fixes, references, touches, supersedes
3. **Ask** — match the question, walk the evidence chain 2 hops, flag superseded decisions
4. **Run anywhere** — the bundled SQLite database needs no credentials, no paid APIs

---

# Demo: a real answer from Django's history

```bash
$ python -m whycode.cli --question \
    "Why does ignore_warnings match substrings by default?"

refused: false   confidence: 0.99

Best match: Fixed #37089 — Made ignore_warnings() match
substrings by default. (commit)

Evidence:
→ fixes      Trac ticket #37089
→ authored by HelmiDev03
```

---

# Demo: the template-tags option

```bash
$ python -m whycode.cli --question \
    "Why is there a transitional option to disable
     multiline template tags?"

refused: false   confidence: 0.86

Best match: Refs #35899 — Added allow_multiline_tags
transitional template option. (commit)

Evidence:
→ references Trac ticket #35899
→ authored by boxed
```

---

# The refusal, honestly demonstrated

```bash
$ python -m whycode.cli --question \
    "Why does Django use a microservices architecture?"

refused: true   confidence: 0.0

No evidence in the graph answers this.
Refusing to invent an answer.
```

> An earlier version answered this from an unrelated docs commit.
> The absent-term rule plus a regression test fixed that for good.

---

# Engineering: runnable, tested, no magic

| | |
|---|---|
| **Graph** | 200 commits · 100 PRs · 100 Trac tickets · 161 files · 90 people · 630 edges |
| **Stack** | Python standard library only · SQLite graph · `gh` CLI |
| **Tests** | 10/10 automated, including refusal and supersession cases |
| **Demo** | Bundled database — runs with zero credentials |

---

# WhyCode — by FORTEC

<div class="text-2xl mt-6">

**Repo:** github.com/eres0045/hackfront-fortec

**Demo:** `python -m whycode.cli --db data/whycode.db --question "Why ...?"`

</div>

<div class="opacity-60 mt-8">
  Built during the hackFront league timeline, from Django's real, public history.
</div>

<div class="mt-8 text-green-400 font-bold text-xl">
  Questions welcome.
</div>
