---
marp: true
theme: gaia
paginate: true
size: 16:9
header: "WhyCode · Team FORTEC"
footer: "hackFront India 2026 · AI and Developer Tools (T-1)"
style: |
  section {
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    padding: 56px 72px;
    color: #1f2937;
  }
  section::after {
    font-size: 14px;
    color: #6b7280;
  }
  header {
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #059669;
  }
  footer {
    font-size: 14px;
    color: #6b7280;
  }
  h1 {
    color: #064e3b;
    border-bottom: 5px solid #10b981;
    padding-bottom: 10px;
    font-size: 46px;
  }
  h2 {
    color: #065f46;
    font-size: 30px;
  }
  strong {
    color: #065f46;
  }
  section.cover {
    background: linear-gradient(135deg, #052e22 0%, #0b1f1a 55%, #14532d 100%);
    color: #f9fafb;
    justify-content: center;
  }
  section.cover h1 {
    color: #ffffff;
    border-bottom: none;
    font-size: 84px;
    line-height: 1.05;
    margin-bottom: 8px;
  }
  section.cover h1::before {
    content: "";
    display: block;
    width: 96px;
    height: 8px;
    background: #4ade80;
    margin-bottom: 28px;
  }
  section.cover p {
    color: #d1fae5;
    font-size: 26px;
  }
  section.cover .tag {
    color: #4ade80;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-size: 20px;
  }
  section.cover .team {
    color: #a7f3d0;
    font-size: 20px;
    margin-top: 36px;
  }
  pre {
    background: #0b1f1a;
    border: 1px solid #14532d;
    border-left: 6px solid #10b981;
    border-radius: 10px;
    padding: 20px 24px;
    font-size: 19px;
    line-height: 1.5;
  }
  pre code {
    color: #d1fae5;
  }
  code {
    font-family: "DejaVu Sans Mono", Consolas, monospace;
  }
  section.refusal {
    background: #fff7f7;
  }
  section.refusal h1 {
    border-bottom-color: #f87171;
  }
  section.refusal blockquote {
    border-left: 6px solid #f87171;
    background: #fef2f2;
    padding: 14px 20px;
    font-size: 22px;
    color: #991b1b;
  }
  table {
    font-size: 22px;
  }
  table th {
    background: #064e3b;
    color: #ffffff;
  }
  table td {
    border-color: #a7f3d0;
  }
---

<!-- _class: cover -->
<!-- _header: "" -->
<!-- _footer: "" -->

# WhyCode

Why is this code like this? Ask its own history.

<span class="tag">Team FORTEC · hackFront India 2026 · AI and Developer Tools (T-1)</span>

<div class="team">Ronit Shrimankar (lead) · Anshul Kamthe · Udita Singh<br>Built on django/django</div>

---

# The problem

- Codebases accumulate **decisions nobody can explain** any more
- A new developer reads an odd function and **guesses** why it exists
- A **wrong guess breaks something** the original author fixed on purpose
- The reasons live **scattered** across commits, pull requests, and tickets — never in one place, never linked to the code they explain

---

# The solution: WhyCode

Ingest a public repo's history into a **graph**, then ask it plain-language *why* questions.

- **Ingest** — commits, PRs, and tickets into one connected store
- **Ask** — get a **cited evidence chain** and a confidence score
- **Refuse** — when the graph holds **no evidence**, it refuses instead of inventing an answer

> No invented answers, ever. The refusal is a feature, not a gap.

---

# How it works

1. **Ingest** — GitHub API via `gh` CLI (commits, PRs) **plus Trac tickets**, since Django uses Trac, not GitHub Issues
2. **Graph** — entities: commit, PR, ticket, file, person · edges: authored, fixes, references, touches, supersedes
3. **Ask** — match the question, walk the evidence chain, flag superseded decisions, refuse when evidence is absent
4. **Runs anywhere** — the bundled SQLite database needs **no credentials, no paid APIs**

---

# Demo: a real answer from Django's history

```bash
$ python -m whycode.cli --question \
    "Why does ignore_warnings match substrings by default?"

refused: false   confidence: 0.99

Best match: Fixed #37089 — Made ignore_warnings()
match substrings by default. (commit)

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

<!-- _class: refusal -->

# The refusal, honestly demonstrated

```bash
$ python -m whycode.cli --question \
    "Why does Django use a microservices architecture?"

refused: true   confidence: 0.0
```

> No evidence in the graph answers this. Refusing to invent an answer.

An earlier version answered this from an unrelated docs commit. The **absent-term rule plus a regression test** fixed that for good.

---

# Engineering: runnable, tested, no magic

| | |
|---|---|
| **Graph** | 200 commits · 100 PRs · 100 Trac tickets · 161 files · 90 people · **630 edges** |
| **Stack** | Python standard library only · SQLite graph · `gh` CLI |
| **Tests** | **10/10** automated, including refusal and supersession cases |
| **Demo** | Bundled database — runs with **zero credentials** |

---

# WhyCode — by FORTEC

**Repo:** github.com/eres0045/hackfront-fortec

**Demo:**

```bash
python -m whycode.cli --db data/whycode.db --question "Why ...?"
```

Built during the hackFront league timeline, from Django's real, public history.

## Questions welcome.
