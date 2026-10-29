# WhyCode demo Q&A (verified against the real Django graph)

Graph: 200 recent commits, 100 PRs, 100 Trac tickets, 161 files,
90 people, 630 edges. Run any question with:

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
("Python 3.15 compatibility."), with every referencing commit shown as
incoming evidence.

## Refused, honestly

**Q: Why does Django use a microservices architecture?**
Refused. The term "microservices" appears in no ingested record, so the
engine refuses instead of answering from the nearest generic match.
An earlier version answered this question from an unrelated docs commit;
the absent-term rule (with a regression test) fixed that.

## Honest limits

- Entities are file-level, not function-level (function parsing is next).
- Django Enhancement Proposals (django/deps) are not ingested yet.
- The graph is local SQLite, not Neo4j AuraDB: judges can run it with
  no accounts or credentials. A Neo4j adapter is a stretch goal, not
  a claim.
