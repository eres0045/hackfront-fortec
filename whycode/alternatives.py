"""WhyCode "Why not" — the rejected alternatives.

Django's DEPs carry an "Alternatives" section naming options that were
proposed and NOT taken, with the reason why (DEP 0009: "These are some
alternative approaches or design decisions that were rejected, with
reasoning why."). This module extracts those options from the DEP bodies
already in the graph — nothing is invented, and a question about an
alternative the record does not contain is a refusal, not a guess.

Formats found in the live DB (27 DEPs, checked 21 Nov 2026):
- Structured sub-headings (DEP 0009: 5 options under ~~~ underlines;
  DEP 0016: 2 options under --- underlines), each followed by prose
  giving the reason.
- Bullet list (DEP 0018: "Alternatives that were considered" + `* ` items)
  — option names only, no per-option reason in the text.
- Prose-only (DEP 0008, DEP 0006): no structured options, so nothing is
  extracted. A sub-heading such as "Summary" is a sibling section, not an
  option, and is excluded by SECTION_WORDS.
"""
import re

# Sub-headings that are sibling sections, never rejected options.
SECTION_WORDS = {
    "summary", "conclusion", "references", "reference implementation",
    "backwards compatibility", "motivation", "rationale", "specification",
    "abstract", "foreword", "appendix", "copyright", "timeline",
    "process", "results", "other concerns", "funding", "future work",
    "reference", "notes",
}

# Words that carry the "why not" mode, not the thing asked about.
WHY_NOT_DROP = {
    "didn", "didnt", "wasn", "wasnt", "isn", "isnt", "doesn", "doesnt",
    "don", "dont", "not", "instead", "rather", "rejected", "reject",
    "choose", "chose", "pick", "picked", "go", "went", "take", "taken",
}

# Tokens too generic to count as naming an alternative ("Fork Django"
# must match on "fork", not on "django" alone).
GENERIC_TOKENS = {"django", "python", "code", "project"}

WHY_NOT_RE = re.compile(
    r"why\s+(didn'?t|did\s+not|wasn'?t|was\s+not|isn'?t|is\s+not"
    r"|doesn'?t|does\s+not)\b|\bwhy\s+not\b|\brejected\b|\binstead\b",
    re.IGNORECASE,
)

REASON_MAX = 600


def is_why_not(question):
    """True when the question asks about something NOT done / rejected."""
    return bool(WHY_NOT_RE.search(question or ""))


def _clean_reason(text):
    """Collapse an RST prose block to plain text, dropping code blocks.

    Lines indented 4+ spaces are literal blocks, `.. ` lines are
    directives, `::` ends a literal-block intro. Inline RST markup
    (``code``, *emphasis*, _links, :roles:) is stripped to the words.
    """
    kept = []
    for line in text.splitlines():
        if line.startswith("    ") or line.startswith("\t"):
            continue
        if line.lstrip().startswith(".. "):
            continue
        if line.rstrip().endswith("::"):
            line = line.rstrip()[:-2]
        kept.append(line)
    out = " ".join(" ".join(kept).split())
    out = re.sub(r"``([^`]+)``", r"\1", out)
    out = re.sub(r"`([^`]+)`_?", r"\1", out)
    out = re.sub(r"\*([^*]+)\*", r"\1", out)
    out = re.sub(r":[a-z-]+:`([^`]+)`", r"\1", out)
    out = re.sub(r"\s+", " ", out).strip()
    if len(out) > REASON_MAX:
        cut = out[:REASON_MAX].rsplit(" ", 1)[0]
        out = cut + " …"
    return out


def _section_bounds(body):
    """Char offsets of the Alternatives section body, or None.

    RST heading: a line reading exactly "Alternatives" followed by an
    underline of =, - or ~. The section ends at the next top-level
    heading (a line followed by a === underline), a Markdown ## heading,
    or the end of the body.
    """
    m = re.search(r"(?m)^Alternatives\s*\n[=\-~]+\s*$", body)
    if not m:
        return None
    tail = body[m.end():]
    ends = []
    top = re.search(r"(?m)^[^\n]+\n=+\s*$", tail)
    if top:
        ends.append(top.start())
    md = re.search(r"(?m)^## ", tail)
    if md:
        ends.append(md.start())
    return (m.end(), m.end() + min(ends)) if ends else (m.end(), len(body))


def _split_options(section):
    """Structured sub-heading options inside an Alternatives section.

    A sub-heading is a line followed by a ~~~ or --- underline. ~~~
    underlines are always options (a deeper level than the section
    heading); --- underlines are options unless the heading is a known
    sibling-section word. Returns [(option, reason_text)].
    """
    found = []
    for m in re.finditer(r"(?m)^([^\n]{2,100})\n([\-~]+)\s*$", section):
        title = m.group(1).strip()
        underline = m.group(2)
        if title.lower() == "alternatives":
            continue
        if underline.startswith("-") and title.lower() in SECTION_WORDS:
            continue
        found.append((m, title))
    options = []
    for i, (m, title) in enumerate(found):
        start = m.end()
        end = found[i + 1][0].start() if i + 1 < len(found) else len(section)
        reason = _clean_reason(section[start:end])
        options.append({"option": title, "reason": reason or None})
    return options


def _bullet_options(body):
    """Bullet-list format: "Alternatives that were considered" + `* ` items.

    Option names only — the DEP gives no per-option reason in the text,
    so reason is None and the answer says so honestly.
    """
    m = re.search(r"(?m)^Alternatives that were considered.*$", body)
    if not m:
        return []
    options = []
    started = False
    for line in body[m.end():].splitlines():
        stripped = line.strip()
        if stripped.startswith("* "):
            started = True
            name = re.sub(r"`([^`]+)`", r"\1", stripped[2:]).strip()
            name = re.sub(r"\s+", " ", name)
            if name:
                options.append({"option": name, "reason": None})
        elif stripped == "" or not started:
            # Blank lines and the intro sentence's continuation lines
            # precede the list; only a non-bullet line AFTER the list
            # ends it.
            continue
        else:
            break
    return options


def extract_alternatives(body):
    """All rejected/considered alternatives named in one DEP body.

    Returns a list of {"option": str, "reason": str | None}. Empty when
    the DEP carries no Alternatives section in a structured form — a
    prose-only Alternatives section is not parsed, because guessing
    which phrases are options would invent options.
    """
    if not body:
        return []
    bounds = _section_bounds(body)
    if bounds is None:
        return _bullet_options(body)
    options = _split_options(body[bounds[0]:bounds[1]])
    if options:
        return options
    return _bullet_options(body)


def _option_tokens(option):
    from whycode.qa import tokens as qa_tokens

    return set(qa_tokens(option))


def find_alternative(store, question):
    """Best-matching rejected alternative for a why-not question.

    Scores every extracted option from every DEP doc in the graph by
    whole-word overlap with the question's non-generic tokens. Returns
    (option_dict, dep_entity, matched_tokens) or None when nothing is
    named: a match must name the option on a specific token, never on
    "django" alone.
    """
    from whycode.qa import tokens as qa_tokens

    qtokens = [t for t in qa_tokens(question) if t not in WHY_NOT_DROP]
    qset = set(qtokens)
    best = None
    for row in store.conn.execute(
            "SELECT * FROM entities WHERE kind = 'doc'").fetchall():
        dep = dict(row)
        for opt in extract_alternatives(dep.get("body") or ""):
            otokens = _option_tokens(opt["option"])
            specific = otokens - GENERIC_TOKENS
            matched = specific & qset
            # The question must name a real share of the option, not one
            # passing word: "Why didn't Django do async?" must not claim
            # "Async modules instead of _async functions" on "async" alone
            # (1 of its 4 specific tokens).
            if not matched or len(matched) / max(1, len(specific)) < 0.5:
                continue
            # First position of any matched token in the question breaks
            # ties towards the option the question is actually about
            # ("Greenlets" beats "Non-asyncio" for "why Greenlets?").
            first_pos = min(qtokens.index(t) for t in matched)
            key = (-len(matched),
                   -len(matched) / max(1, len(specific)),
                   first_pos)
            if best is None or key < best[0]:
                best = (key, opt, dep, matched)
    if best is None:
        return None
    _, opt, dep, matched = best
    return opt, dep, matched


def answer_why_not(store, question):
    """Answer a why-not question from the DEP record, or refuse.

    The claim is the DEP's own Alternatives text, quoted verbatim and
    cited to the DEP. When the option has no reason in the text the
    answer says so instead of supplying one.
    """
    from whycode.qa import REFUSAL, evidence_chain

    found = find_alternative(store, question)
    if found is None:
        return {"question": question, "refused": True, "mode": "why_not",
                "reason": REFUSAL + " No rejected alternative in the "
                "graph matches what was asked about.",
                "confidence": 0.0, "evidence": []}
    opt, dep, matched = found
    specific = _option_tokens(opt["option"]) - GENERIC_TOKENS
    confidence = round(min(0.99, len(matched) / max(1, len(specific))), 2)
    if opt["reason"]:
        answer = (f"Not taken: {opt['option']}. In {dep['title']}, Django "
                  f"considered this alternative and did not take it: "
                  f"\u201c{opt['reason']}\u201d")
    else:
        answer = (f"Not taken: {opt['option']}. {dep['title']} lists this "
                  f"among the alternatives considered, but gives no "
                  f"per-option reason in its text.")
    return {"question": question, "refused": False, "mode": "why_not",
            "answer": answer, "confidence": confidence,
            "evidence": evidence_chain(store, dep["id"]), "match": dep,
            "rejected": {"option": opt["option"], "reason": opt["reason"],
                         "dep_title": dep["title"], "dep_url": dep["url"]}}
