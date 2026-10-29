# WhyCode demo Q&A (verified against the real Django graph)

Graph: 200 recent commits, 100 PRs, 100 Trac tickets, 161 files,
90 people, 27 design docs (Django Enhancement Proposals), 641 edges.
Run any question with:

```text
python3 -m whycode.cli --db data/whycode.db --question "Why ...?"
```

## Answered from evidence

**Q: Why does ignore_warnings match substrings by default?**
Confidence 0.99, 8 evidence records. Best match: commit
"Fixed #37089 -- Made ignore_warnings() match substrings by default",
linked by a fixes edge to Trac ticket #37089
("ignore_warnings() handles message arg differently from other test
helpers") plus the author and the touching files.

**Q: Why is there a transitional option to disable multiline template tags?**
Confidence 0.86, 6 evidence records. Best match: commit
"Refs #35899 -- Added allow_multiline_tags transitional template option",
linked to Trac ticket #35899 ("Allow newlines in {% %} tags").

**Q: Why is Python 3.15 compatibility being added?**
Confidence 0.99, 26 evidence records. Best match is now DEP 0018
(Dictionary-based MAILERS setting and mailers factory), which ties
Trac ticket #36664 ("Python 3.15 compatibility.") at 4/4 matched
question terms; the tie is broken by entity-id order, so the DEP
surfaces first. Before the DEP upgrade the best match was Trac
ticket #36664 with 25 evidence records. Confidence is unchanged.

## Answered from a design doc (new in the DEP upgrade)

**Q: Why does Django have a simplified routing syntax?**
Confidence 0.99, 3 evidence records. Best match: DEP 0201
("Simplified routing syntax", final), matched 5/5 question terms.
Evidence chain: DEP 0201 mentions `django/core/signing.py`, which
is touched by a commit, which links back to DEP 0201.

## Refused, honestly

**Q: Why does Django use quasiflobber?**
Refused. The term "quasiflobber" appears in no ingested record, so
the engine refuses instead of answering from the nearest generic match.

**Behavior change, recorded honestly (DEP upgrade, 2026-10-29):**
the old refusal demo, "Why does Django use a microservices
architecture?", NO LONGER refuses. DEP 0009 (Async-capable Django)
mentions "microservices" in passing ("calling out to a series of
microservices"), so every question term now appears somewhere in
the graph and the engine answers: confidence 0.99, best match
DEP 0009, 0 evidence records (that DEP has no edges). The demo
video's refusal segment is therefore stale: it shows a refusal
for a question the upgraded engine now answers. The refusal rule
itself is unchanged — a question with any term absent from the
graph still refuses, as the quasiflobber question above proves.

## Honest limits

- Entities are file-level, not function-level (function parsing is next).
- 27 DEPs are ingested as doc entities with 11 mentions edges to
  files they name, but DEP answers can have thin evidence chains:
  most DEPs have no edges at all, and ranking is token-count then
  entity-id, so a token-count tie can surface an incidental match
  (the mailers DEP for the Python 3.15 question above).
- The graph is local SQLite, not Neo4j AuraDB: judges can run it with
  no accounts or credentials. A Neo4j adapter is a stretch goal, not
  a claim.
