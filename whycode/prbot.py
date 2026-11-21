"""WhyCode GitHub PR bot — a cited decision on the PRs that need one.

A Flask webhook receiver (route /github-webhook in app.py). On a
pull_request opened / synchronised event it takes the PR's changed
files from the GitHub REST API, looks up decisions governing those
files in the WhyCode graph, and posts ONE comment — only when there
is a cited decision to surface. It never comments on every PR, never
blocks a merge (advise only), and never comments twice on the same
PR (it checks for its own marker in the existing comments first).

Rules, enforced here:
- A comment needs a real cited decision: a doc (DEP) mentioning the
  file, or a commit touching it with a linked issue. A file with
  nothing in the graph gets no comment — silence, not a guess.
- The comment quotes the decision's own title from the graph, shows
  the blast radius for the file, and names who to talk to. Nothing
  in it is generated prose about the code.
- GitHub API access is the raw REST API via requests (Apache-2.0).
  PyGithub is LGPL-3.0 and is never used here.
- The GitHub token comes from the GITHUB_TOKEN environment variable
  only — never logged, never written to a file, never in a response.
- If GITHUB_WEBHOOK_SECRET is set, the X-Hub-Signature-256 HMAC is
  verified and a bad signature is a 401. If it is unset the webhook
  accepts unsigned deliveries (documented, not hidden).
"""
import hashlib
import hmac

import requests
from whycode.features import blast_radius as _blast_radius
from whycode.features import who_to_ask as _who_to_ask

MARKER = "<!-- whycode-pr-bot -->"
GITHUB_API = "https://api.github.com"


def verify_signature(secret, body, signature):
    """True when the HMAC-SHA256 signature matches the body.

    `signature` is the X-Hub-Signature-256 header ("sha256=<hex>").
    A missing secret means verification is off (see module docstring).
    """
    if not secret:
        return True
    if not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature[7:])


def github_api(token, method, path, json_body=None):
    """One raw GitHub REST call. Returns (status, parsed JSON)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.request(
        method, GITHUB_API + path, headers=headers, json=json_body,
        timeout=30)
    try:
        data = resp.json()
    except ValueError:
        data = {}
    return resp.status_code, data


def find_decision_for_files(store, paths):
    """The cited decision governing one of these files, or None.

    For each path (in PR order): a doc mentioning the file wins
    (a formal decision record); otherwise the most recent commit
    touching it, with the issue it fixes. Returns
    {"kind": "doc"|"commit", "title", "url", "date", "issue": ...}.
    """
    for path in paths:
        file_id = f"file:{path[5:] if path.startswith('file:') else path}"
        if not store.get_entity(file_id):
            continue
        docs = []
        commits = []
        for nb in store.neighbors_reverse(file_id):
            if nb.get("kind") == "doc" and nb.get("relation") == "mentions":
                docs.append(nb)
            elif (nb.get("kind") == "commit"
                    and nb.get("relation") == "touches"):
                commits.append(nb)
        if docs:
            docs.sort(key=lambda d: d["id"])
            doc = docs[0]
            return {"kind": "doc", "title": doc["title"],
                    "url": doc.get("url") or "",
                    "date": (doc.get("created_at") or "")[:10],
                    "issue": None}
        if commits:
            commits.sort(key=lambda c: c.get("created_at") or "",
                         reverse=True)
            commit = commits[0]
            issue = None
            for nb in store.neighbors(commit["id"]):
                if (nb.get("kind") in ("issue", "pr")
                        and nb.get("relation") in ("fixes", "references")):
                    issue = {"id": nb["id"], "title": nb["title"],
                             "url": nb.get("url") or ""}
                    break
            return {"kind": "commit", "title": commit["title"],
                    "url": commit.get("url") or "",
                    "date": (commit.get("created_at") or "")[:10],
                    "issue": issue}
    return None


def build_comment(store, paths):
    """The PR comment markdown for these changed files, or None.

    None means no cited decision governs any of them — the bot stays
    silent. The comment cites the decision, shows the blast radius
    for the first governed file, and names who to talk to.
    """
    decision = find_decision_for_files(store, paths)
    if not decision:
        return None
    governed = [p for p in paths
                if store.get_entity(
                    f"file:{p[5:] if p.startswith('file:') else p}")]
    first = governed[0]
    match = store.get_entity(
        f"file:{first[5:] if first.startswith('file:') else first}")
    blast = _blast_radius(store, match, evidence=[])
    talk_to = _who_to_ask(blast)
    lines = [
        "## WhyCode — a decision governs this PR",
        "",
        f"This PR touches `{first}`, which is governed by:",
        "",
    ]
    if decision["kind"] == "doc":
        lines.append(f"**{decision['title']}** (formal decision record"
                     + (f", {decision['date']}" if decision["date"] else "")
                     + ")")
    else:
        lines.append(f"**{decision['title']}** (commit"
                     + (f", {decision['date']}" if decision["date"] else "")
                     + ")")
    if decision["url"]:
        lines[-1] += f" — <{decision['url']}>"
    if decision["issue"]:
        lines.append("")
        lines.append(f"Linked record: **{decision['issue']['title']}**"
                     + (f" — <{decision['issue']['url']}>"
                        if decision["issue"]["url"] else ""))
    lines.append("")
    lines.append(
        f"**Blast radius:** {blast['file_count']} file(s), "
        f"{blast['commit_count']} commit(s), "
        f"{blast['issue_count']} issue(s) / PR(s)"
        + (f", {blast['decision_count']} related decision(s)"
           if blast["decision_count"] else "")
        + ".")
    if talk_to:
        lines.append(
            "Talk to: " + ", ".join(
                f"{p['title']} ({p['count']} commit"
                f"{'s' if p['count'] != 1 else ''})" for p in talk_to)
            + " before changing this code.")
    lines.append("")
    lines.append(
        "_Posted by WhyCode — every claim here is cited from the "
        "django/django history graph, or the bot stays silent._")
    lines.append(MARKER)
    return "\n".join(lines)


def handle_pull_request(store, token, repo, pr_number):
    """Fetch the PR's files, comment once if a decision governs them.

    Returns ("commented" | "no_decision" | "already_commented",
    detail). Raises on GitHub API failure so the caller can 502.
    """
    status, files_data = github_api(
        token, "GET", f"/repos/{repo}/pulls/{pr_number}/files")
    if status != 200:
        raise RuntimeError(
            f"GitHub files lookup failed: HTTP {status}")
    paths = [f["filename"] for f in files_data]
    comment = build_comment(store, paths)
    if comment is None:
        return "no_decision", "no cited decision governs these files"
    status, comments = github_api(
        token, "GET", f"/repos/{repo}/issues/{pr_number}/comments")
    if status != 200:
        raise RuntimeError(
            f"GitHub comments lookup failed: HTTP {status}")
    for c in comments:
        if MARKER in (c.get("body") or ""):
            return "already_commented", "WhyCode already commented here"
    status, _ = github_api(
        token, "POST", f"/repos/{repo}/issues/{pr_number}/comments",
        {"body": comment})
    if status not in (200, 201):
        raise RuntimeError(f"GitHub comment post failed: HTTP {status}")
    return "commented", comment[:120]
