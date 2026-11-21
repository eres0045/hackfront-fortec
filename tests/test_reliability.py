"""Reliability tests: input validation + per-IP rate limiting.

Covers the Build Plan "Reliability & access" commitments: empty /
over-long / garbage questions get friendly handling (never a 500), and
the question route rate-limits at 30 requests/minute/IP with a 429.

The limiter is bypassed while Flask TESTING is on (so the suite stays
fast); the rate-limit tests flip TESTING off for their duration, with a
unique IP each, so the real limit path runs. Run:
python3 -m pytest tests/ -q
"""
import pytest

import app as ui_app

Q1 = "Why does ignore_warnings match substrings by default?"
Q2 = "Why does Django use microservices?"


@pytest.fixture()
def client():
    ui_app.app.config["TESTING"] = True
    with ui_app.app.test_client() as c:
        yield c


@pytest.fixture()
def live_client():
    """Client with the rate limiter actually armed (TESTING off)."""
    ui_app.app.config["TESTING"] = False
    ui_app.reset_rate_limits()
    with ui_app.app.test_client() as c:
        yield c
    ui_app.app.config["TESTING"] = True
    ui_app.reset_rate_limits()


# --- Input validation ------------------------------------------------------

def test_empty_get_question_shows_notice(client):
    r = client.get("/?q=")
    assert r.status_code == 200
    assert b"Type a question first" in r.data
    assert b"WhyCode refuses" not in r.data


def test_whitespace_get_question_shows_notice(client):
    r = client.get("/?q=%20%20%20")
    assert r.status_code == 200
    assert b"Type a question first" in r.data


def test_over_long_post_question_gets_too_long_message(client):
    q = "why does django " * 40  # 640 chars
    assert len(q) > ui_app.MAX_QUESTION_LENGTH
    r = client.post("/", data={"question": q})
    assert r.status_code == 200
    assert b"too long" in r.data
    assert b"500" in r.data
    # Never run through the engine: no answer, no refusal card.
    assert b"WhyCode refuses" not in r.data
    assert b"99%" not in r.data


def test_over_long_get_question_gets_too_long_message(client):
    q = "x" * 501
    r = client.get(f"/?q={q}")
    assert r.status_code == 200
    assert b"too long" in r.data


def test_exactly_500_chars_is_not_too_long(client):
    q = "why django ignore_warnings " * 18 + "django django "
    assert len(q) == ui_app.MAX_QUESTION_LENGTH
    r = client.post("/", data={"question": q})
    assert r.status_code == 200
    assert b"too long" not in r.data


def test_garbage_punctuation_shows_refusal_card(client):
    r = client.post("/", data={"question": "!!! ??? *** ###"})
    assert r.status_code == 200
    assert b"WhyCode refuses to answer this" in r.data
    assert b"Refusing to invent an answer" in r.data


def test_garbage_digits_only_shows_refusal_card(client):
    r = client.post("/", data={"question": "123456789"})
    assert r.status_code == 200
    assert b"WhyCode refuses to answer this" in r.data
    assert b"appears in no ingested record" in r.data


def test_garbage_get_question_shows_refusal_card(client):
    r = client.get("/?q=%21%21%21")
    assert r.status_code == 200
    assert b"WhyCode refuses to answer this" in r.data


# --- Rate limiting ---------------------------------------------------------

def test_normal_demo_flow_not_limited(live_client):
    ip = "203.0.113.10"
    for q in (Q1, Q2, Q1, Q2, Q1):
        r = live_client.post("/", data={"question": q},
                            environ_base={"REMOTE_ADDR": ip})
        assert r.status_code == 200


def test_rate_limit_trips_after_threshold(live_client):
    ip = "203.0.113.11"
    for _ in range(ui_app.RATE_LIMIT_REQUESTS):
        r = live_client.get("/", environ_base={"REMOTE_ADDR": ip})
        assert r.status_code == 200
    r = live_client.get("/", environ_base={"REMOTE_ADDR": ip})
    assert r.status_code == 429
    assert b"Slow down" in r.data
    assert b"Try again in a moment" in r.data
    assert r.headers.get("Retry-After") == str(ui_app.RATE_LIMIT_WINDOW)


def test_rate_limit_is_per_ip(live_client):
    limited_ip = "203.0.113.12"
    other_ip = "203.0.113.13"
    for _ in range(ui_app.RATE_LIMIT_REQUESTS):
        live_client.get("/", environ_base={"REMOTE_ADDR": limited_ip})
    r = live_client.get("/", environ_base={"REMOTE_ADDR": limited_ip})
    assert r.status_code == 429
    r = live_client.get("/", environ_base={"REMOTE_ADDR": other_ip})
    assert r.status_code == 200


def test_rate_limit_does_not_cover_robots_or_sitemap(live_client):
    ip = "203.0.113.14"
    for _ in range(ui_app.RATE_LIMIT_REQUESTS):
        live_client.get("/", environ_base={"REMOTE_ADDR": ip})
    r = live_client.get("/", environ_base={"REMOTE_ADDR": ip})
    assert r.status_code == 429
    assert live_client.get("/robots.txt",
                           environ_base={"REMOTE_ADDR": ip}).status_code == 200
    assert live_client.get("/sitemap.xml",
                           environ_base={"REMOTE_ADDR": ip}).status_code == 200
