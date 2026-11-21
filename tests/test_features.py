"""Feature tests: "Why not" (rejected alternatives) + decision timeline.

The DEP body fixtures below are short verbatim excerpts of real Django
DEP text (DEP 0009, DEP 0016, DEP 0018) — the extraction must work on
the real RST, not on a cleaned-up imitation.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as ui_app
from whycode.alternatives import (
    answer_why_not,
    extract_alternatives,
    is_why_not,
)
from whycode.graph import GraphStore
from whycode.qa import ask, decision_timeline

DEP0009_BODY = """\
:DEP: 0009
:Status: Accepted
:Created: 2019-05-06

Alternatives
------------

These are some alternative approaches or design decisions that were rejected,
with reasoning why.

Async modules instead of _async functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of the rather ugly suffixing of methods and functions that need both
an async and a sync variant, we could instead create whole separate async
namespaces with things called by the same name, and just have import paths
change::

    from django.core.cache_async import cache
    cache.get("foo")

This is cleaner, but the problem comes when trying to use both sync and async
versions in the same file.

Fork Django
~~~~~~~~~~~

A hard fork is unsustainable, and also a massive waste of resources; it's likely
that it would be near-impossible to merge the result back in, given the huge
deviation, and splitting the user and support base is a terrible idea.

Extend Channels
~~~~~~~~~~~~~~~

A popular option people have often suggested is to extend Channels to achieve
many of these goals "external" to Django.

Non-asyncio
~~~~~~~~~~~

There are other async frameworks and event loops for Python that are not
``asyncio``, and that have often made better design decisions for the type of
usage that Django wants to do. The ``await`` and ``async`` keywords in Python
are actually independent of the event loop and implementation running underneath
them.

Greenlets/Gevent
~~~~~~~~~~~~~~~~

It's worth talking about greenlets and Gevent specifically, as they are an
implementation of concurrent Python code that does not use the Python async
syntax.

While the idea of having methods and functions seems attractive at first, there
are many subtle problems with the greenlet-based approach. The lack of an
explicit ``yield`` or ``await`` means that a complex API like Django's basically
becomes unpredictable as to knowing if it will block the current execution
context or not.

Backwards Compatibility
=======================

Django remains backwards compatible.
"""

DEP0016_BODY = """\
:DEP: 0016
:Created: 2025-01-07

Alternatives
============

Beside the status quo, some other possibilities compete with this proposal.

Only add an alias
-----------------

This could be a less invasive change by only adding the new command name,
and not modifying the documentation.

Reserve the name
----------------

``django-admin`` is only commonly used directly to create new projects.

Backwards Compatibility
=======================

Nothing changes for existing users.
"""

DEP0018_BODY = """\
Alternatives that were considered—either at DjangoCon Europe 2024 or in the
later discussions—include:

* `EMAIL_PROVIDERS` and `mail.providers`
* `EMAILS` and `mail.email_backends` or `mail.connections`
* `EMAIL_SERVICES` and `mail.services`

The discussion linked above covers arguments for and against these options.
"""

DEP_NO_ALT_BODY = """\
:DEP: 0002
:Created: 2014-12-05

Abstract
========

This DEP proposes experimental APIs.

Specification
=============

Details go here.
"""


def alt_store():
    s = GraphStore()
    s.add_entity("dep:0009-async", "doc", "DEP 0009: Async-capable Django",
                 DEP0009_BODY,
                 "https://github.com/django/deps/blob/main/accepted/0009-async.rst")
    s.add_entity("dep:0016-name-main-command-django",
                 "doc", "DEP 0016: Name the main command `django`",
                 DEP0016_BODY, "https://example.com/dep0016")
    s.add_entity("dep:0018-mailers",
                 "doc", "DEP 0018: Dictionary-based MAILERS setting",
                 DEP0018_BODY, "https://example.com/dep0018")
    s.add_entity("dep:0002-experimental-apis", "doc",
                 "DEP 0002: Experimental APIs", DEP_NO_ALT_BODY,
                 "https://example.com/dep0002")
    return s


# --- extraction -----------------------------------------------------------

def test_extract_dep0009_five_options():
    opts = extract_alternatives(DEP0009_BODY)
    names = [o["option"] for o in opts]
    assert names == ["Async modules instead of _async functions",
                     "Fork Django", "Extend Channels", "Non-asyncio",
                     "Greenlets/Gevent"]
    fork = [o for o in opts if o["option"] == "Fork Django"][0]
    assert "unsustainable" in fork["reason"]
    # The literal code block must not leak into a reason.
    async_mod = [o for o in opts
                 if o["option"].startswith("Async modules")][0]
    assert "cache_async" not in async_mod["reason"]
    assert "import paths change" in async_mod["reason"]


def test_extract_dep0016_two_options():
    opts = extract_alternatives(DEP0016_BODY)
    names = [o["option"] for o in opts]
    assert names == ["Only add an alias", "Reserve the name"]
    assert "less invasive" in opts[0]["reason"]


def test_extract_bullet_list_has_names_but_no_reasons():
    opts = extract_alternatives(DEP0018_BODY)
    assert len(opts) == 3
    assert opts[0]["option"] == "EMAIL_PROVIDERS and mail.providers"
    assert all(o["reason"] is None for o in opts)


def test_extract_no_alternatives_section_is_empty():
    assert extract_alternatives(DEP_NO_ALT_BODY) == []
    assert extract_alternatives("") == []


# --- why-not answering ----------------------------------------------------

def test_is_why_not_detection():
    assert is_why_not("Why didn't Django fork instead of adding async?")
    assert is_why_not("Why was Greenlets rejected?")
    assert is_why_not("Why not use Channels instead?")
    assert not is_why_not("Why does ignore_warnings match substrings?")
    assert not is_why_not("Why does Django use microservices?")


def test_why_not_demo_question_answers_from_dep0009():
    r = answer_why_not(alt_store(),
                       "Why didn't Django fork instead of adding async?")
    assert not r["refused"]
    assert r["mode"] == "why_not"
    assert r["rejected"]["option"] == "Fork Django"
    assert r["rejected"]["dep_title"] == "DEP 0009: Async-capable Django"
    assert "unsustainable" in r["rejected"]["reason"]
    assert "Fork Django" in r["answer"]
    assert r["confidence"] > 0.9


def test_why_not_greenlets_beats_non_asyncio():
    r = answer_why_not(
        alt_store(), "Why didn't Django use Greenlets instead of asyncio?")
    assert not r["refused"]
    assert r["rejected"]["option"] == "Greenlets/Gevent" or \
        "Greenlets" in r["rejected"]["option"]


def test_why_not_unknown_alternative_refuses():
    r = answer_why_not(alt_store(),
                       "Why didn't Django rewrite everything in Rust?")
    assert r["refused"]
    assert "No rejected alternative" in r["reason"]


def test_ask_routes_why_not_first_but_falls_back():
    # A why-not phrasing with no matching alternative falls back to the
    # normal engine instead of refusing outright: the DEP has no chain,
    # so the normal engine refuses on its own (empty evidence chain).
    r = ask(alt_store(), "Why didn't Django do async?")
    assert r["refused"]
    # And the headline demo question works through ask() too.
    r = ask(alt_store(),
            "Why didn't Django fork instead of adding async?")
    assert not r["refused"]
    assert r["rejected"]["option"] == "Fork Django"


def test_why_not_never_matches_on_django_alone():
    # "Why didn't Django do async?" must not answer "Fork Django" just
    # because the option contains the word Django.
    r = answer_why_not(alt_store(), "Why didn't Django do async?")
    assert r["refused"]


# --- decision timeline ----------------------------------------------------

def timeline_store():
    s = GraphStore()
    s.add_entity("dep:0009-async", "doc", "DEP 0009: Async-capable Django",
                 DEP0009_BODY,
                 "https://github.com/django/deps/blob/main/accepted/0009-async.rst")
    s.add_entity("c1", "commit", "Fixed #37089 -- Added async support",
                 "", "u/c1", created_at="2020-06-15T10:00:00Z")
    s.add_entity("p9", "pr", "Add async views",
                 "", "u/p9", created_at="2019-11-02T09:00:00Z")
    s.add_entity("i9", "issue", "Async support tracking ticket",
                 "", "u/i9")  # no date: must be omitted, never guessed
    s.add_edge("c1", "dep:0009-async", "references")
    s.add_edge("p9", "dep:0009-async", "references")
    s.add_edge("i9", "dep:0009-async", "references")
    return s


def test_timeline_sorted_oldest_first_and_undated_omitted():
    s = timeline_store()
    match = s.get_entity("dep:0009-async")
    from whycode.qa import evidence_chain
    tl = decision_timeline(s, match, evidence_chain(s, "dep:0009-async"))
    dates = [e["date"] for e in tl]
    assert dates == sorted(dates)
    assert dates[0] == "2019-05-06"  # DEP :Created:, parsed from the body
    assert "2019-11-02" in dates[1]
    assert "2020-06-15" in dates[2]
    assert all(e["title"] != "Async support tracking ticket" for e in tl)
    assert all(e["date"] for e in tl)


def test_timeline_superseded_label():
    s = timeline_store()
    s.add_entity("dep:9999-test", "doc", "DEP 9999: Test successor",
                 ":Created: 2021-01-10\n", "u/dep9999")
    s.add_edge("dep:0009-async", "dep:9999-test", "supersedes")
    match = s.get_entity("dep:0009-async")
    from whycode.qa import evidence_chain
    tl = decision_timeline(s, match, evidence_chain(s, "dep:0009-async"))
    newer = [e for e in tl if e["title"] == "DEP 9999: Test successor"]
    assert newer and newer[0]["label"] == "Supersedes an earlier decision"


# --- UI -------------------------------------------------------------------

@pytest.fixture()
def client():
    ui_app.app.config["TESTING"] = True
    with ui_app.app.test_client() as c:
        yield c


def test_ui_why_not_card_renders_live(client):
    r = client.post(
        "/", data={"question": "Why didn't Django fork instead of adding async?"})
    assert r.status_code == 200
    assert b"Why not" in r.data
    assert b"Fork Django" in r.data
    assert b"unsustainable" in r.data
    assert b"DEP 0009" in r.data
    assert b"Alternatives section" in r.data


def test_ui_timeline_renders_on_q1(client):
    r = client.post(
        "/", data={"question": "Why does ignore_warnings match substrings by default?"})
    assert r.status_code == 200
    assert b"Decision timeline" in r.data
    assert b"99%" in r.data


def test_ui_fork_question_is_an_example_chip(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Why didn" in r.data and b"fork instead of adding async" in r.data
