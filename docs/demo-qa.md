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
Confidence 0.99, 25 evidence records. Best match: Trac ticket #36664
("Python 3.15 compatibility."). It ties DEP 0018 (Dictionary-based
MAILERS setting and mailers factory) at 4/4 matched question terms,
but the tie is broken by title hits: the ticket's title is about
Python 3.15, the DEP's title is about mailers. Ranking is
matched-token count, then title hits, then evidence-chain size, then
entity-id order. (Before the ranking fix the tie fell to entity-id
order and the DEP surfaced first.)

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
  matches: token-count, then title hits, then chain size — a doc that
  merely mentions a term loses to a record whose title is about it,
  and a record with no chain at all refuses instead of answering.
- The graph is local SQLite, not Neo4j AuraDB: judges can run it with
  no accounts or credentials. A Neo4j adapter is a stretch goal, not
  a claim.
