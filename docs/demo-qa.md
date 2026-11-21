# WhyCode demo Q&A (verified against the real Django graph)

Graph: 200 recent commits, 100 PRs, 100 Trac tickets, 161 files,
90 people, 27 design docs (Django Enhancement Proposals), 644 edges
(including 3 supersedes edges read from the DEP text itself: DEP 0019
supersedes DEP 10 and DEP 12; DEP 0020 supersedes DEP 4).
Run any question with:

```text
python3 -m whycode.cli --db data/whycode.db --question "Why ...?"
```

## Answered from evidence

**Q: Why does ignore_warnings match substrings by default?**
Confidence 0.99, 3 evidence records. Best match: commit
"Fixed #37089 -- Made ignore_warnings() match substrings by default",
linked by a fixes edge to Trac ticket #37089
("ignore_warnings() handles message arg differently from other test
helpers"), plus the author and the test-coverage commit that references
the same ticket. (Before the chain cleanup this was 8 records: the
same-author PR "Added gettext to PATH in Windows CI" and the best
match's duplicate of itself are gone.)

**Q: Why is there a transitional option to disable multiline template tags?**
Confidence 0.86, 3 evidence records. Best match: commit
"Refs #35899 -- Added allow_multiline_tags transitional template option",
linked to Trac ticket #35899 ("Allow newlines in {% %} tags").

**Q: Why is Python 3.15 compatibility being added?**
Confidence 0.99, 10 evidence records. Best match: Trac ticket #36664
("Python 3.15 compatibility."). It ties DEP 0018 (Dictionary-based
MAILERS setting and mailers factory) at 4/4 matched question terms,
but the tie is broken by BM25: the ticket's title is about
Python 3.15, the DEP's title is about mailers. Ranking is BM25 over
title (counted twice) + body, within the maximal token-coverage tier;
title hits, then chain size, break ties. (Before the ranking fix the tie fell to entity-id
order and the DEP surfaced first.)

## Answered from a design doc (new in the DEP upgrade)

**Q: Why does Django have a simplified routing syntax?**
Confidence 0.99, 2 evidence records. Best match: DEP 0201
("Simplified routing syntax", final), matched 5/5 question terms.
Evidence chain: DEP 0201 mentions `django/core/signing.py`, which
is touched by a commit. (Before the chain cleanup this was 3 records:
the chain used to link back to DEP 0201 itself.)

**Q: Why does Django need a steering council?**
Confidence 0.99, 2 evidence records. Best match: DEP 0012
("The Steering Council"). The answer carries the superseded banner:
this decision was superseded by DEP 0019 ("Technical governance for
the Django project") — a real edge read from DEP 0019's own text
("This document supersedes both DEP 10 and DEP 12"). Two more real
edges: DEP 0020 supersedes DEP 4 (ask "Why does Django follow a
time-based release schedule?"), and DEP 0010 is superseded by DEP 0019
(ask "Why does Django have technical governance?").

## Refused, honestly

**Q: Why does Django use quasiflobber?**
Refused. The term "quasiflobber" appears in no ingested record, so
the engine refuses instead of answering from the nearest generic match.

**Ranking fix, recorded honestly (2026-10-29):** the microservices
question refuses again. DEP 0009 (Async-capable Django) mentions
"microservices" in passing, so every question term appears somewhere
in the graph, but that DEP has no edges — and a best match with an
empty evidence chain is now a refusal, not an answer, because a claim
with zero linked records behind it is not an evidenced answer. The
demo video's refusal segment is valid again: it shows exactly this
refusal. The refusal rule itself is unchanged — a question with any
term absent from the graph still refuses, as the quasiflobber
question above proves.

## Honest limits

- Entities are file-level, not function-level (function parsing is next).
- 27 DEPs are ingested as doc entities with 11 mentions edges to
  files they name, but DEP answers can have thin evidence chains:
  most DEPs have no edges at all. Ranking guards against incidental
  matches: BM25 over title (counted twice) + body, within the maximal
  token-coverage tier — a doc that merely mentions a term loses to a
  record whose title is about it, and a record with no chain at all
  refuses instead of answering.
- The graph is local SQLite, not Neo4j AuraDB: judges can run it with
  no accounts or credentials. A Neo4j adapter is a stretch goal, not
  a claim.
