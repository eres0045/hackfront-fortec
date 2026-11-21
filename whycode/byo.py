"""Bring-your-own-repo ingest for WhyCode.

A visitor pastes a public GitHub repo URL; we clone its HISTORY ONLY
(commits + files + authors) into a per-repo SQLite graph and answer
questions about it with the same engine as the Django demo.

Deliberately NOT included: PRs and issues (those need GitHub API auth
— out of scope for the finale), private repos (no tokens exist, and
none are ever stored), and file contents (blobs are never downloaded:
git clones with --filter=blob:none, dulwich reads trees only).

Nothing from the repo is ever executed: we read commit metadata and
tree paths only, through the git CLI or dulwich — never file contents,
never hooks, never repo code.
"""
import concurrent.futures
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

from whycode.graph import GraphStore

MAX_COMMITS = 300
INGEST_TIMEOUT = 90  # seconds, whole ingest (clone + build)
MAX_REPOS = 3  # stored repos; a 4th ingest deletes the oldest
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEGMENT_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$")
GIT_URL_RE = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)"
    r"(?:\.git)?/?$")


class IngestError(Exception):
    """User-facing ingest failure (message is shown to the visitor)."""


def parse_github_url(url):
    """(owner, repo) for a public GitHub repo URL, or None.

    Accepts https://github.com/<owner>/<repo> with an optional
    trailing slash or .git suffix. Anything else — other hosts,
    http, ssh (git@), extra path segments — is rejected.
    """
    if not url or not isinstance(url, str):
        return None
    m = GIT_URL_RE.match(url.strip())
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    if (not SEGMENT_RE.match(owner) or not SEGMENT_RE.match(repo)
            or len(owner) > 100 or len(repo) > 100):
        return None
    return owner, repo


def repo_slug(owner, repo):
    """Filesystem-safe slug for a repo: owner__repo."""
    return f"{owner}__{repo}"


_repos_dir_cache = None


def repos_dir():
    """Where per-repo DBs + the registry live.

    data/repos/ when it is writable (normal case on Render); the
    system temp dir when it is not (the Embarko container runs as a
    non-root user over root-owned files, so /app may be read-only).
    WHYCODE_REPOS_DIR overrides both (tests). Resolved once per
    process.
    """
    global _repos_dir_cache
    if _repos_dir_cache is not None:
        return _repos_dir_cache
    override = os.environ.get("WHYCODE_REPOS_DIR")
    candidates = []
    if override:
        candidates.append(override)
    candidates.append(os.path.join(BASE_DIR, "data", "repos"))
    for path in candidates:
        try:
            os.makedirs(path, exist_ok=True)
            probe = os.path.join(path, ".write-test")
            with open(probe, "w") as f:
                f.write("ok")
            os.remove(probe)
            _repos_dir_cache = path
            return path
        except OSError:
            continue
    fallback = os.path.join(tempfile.gettempdir(), "whycode-repos")
    os.makedirs(fallback, exist_ok=True)
    _repos_dir_cache = fallback
    return fallback


def reset_repos_dir_cache():
    """Forget the resolved repos dir (tests only)."""
    global _repos_dir_cache
    _repos_dir_cache = None


def repo_db_path(owner, repo):
    return os.path.join(repos_dir(), repo_slug(owner, repo) + ".db")


def repo_exists(owner, repo):
    return os.path.isfile(repo_db_path(owner, repo))


def _registry_path():
    return os.path.join(repos_dir(), "registry.json")


def _load_registry():
    try:
        with open(_registry_path()) as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("repos"), list):
            return data["repos"]
    except (OSError, ValueError):
        pass
    return []


def _save_registry(entries):
    tmp = _registry_path() + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"repos": entries}, f)
    os.replace(tmp, _registry_path())


def _register(owner, repo, commits, entities):
    # Entries stay oldest-first by ingestion order (ingested_at ties
    # within the same second are common — sorting by timestamp alone
    # pruned the NEWEST entry instead of the oldest).
    entries = [e for e in _load_registry()
               if e.get("slug") != repo_slug(owner, repo)]
    entries.append({
        "slug": repo_slug(owner, repo), "owner": owner, "repo": repo,
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commits": commits, "entities": entities,
    })
    for stale in entries[:-MAX_REPOS]:
        try:
            os.remove(os.path.join(repos_dir(), stale["slug"] + ".db"))
        except OSError:
            pass
    _save_registry(entries[-MAX_REPOS:])


def _remaining(deadline):
    return max(5.0, deadline - time.monotonic())


def _fetch_with_git(url, tmpdir, deadline):
    """Commit records via the git CLI (fast path; needs the binary).

    Clone is --filter=blob:none (no file contents) + --no-checkout
    (no working tree) + --depth 300. Two `git log` calls: one for
    commit metadata, one (COMMIT markers) for the files each commit
    touched. Returns [{sha, name, email, date, title, body, files}].
    """
    subprocess.run(
        ["git", "clone", "--filter=blob:none", "--no-checkout",
         "--depth", str(MAX_COMMITS), url, tmpdir],
        check=True, timeout=_remaining(deadline),
        capture_output=True, text=True)
    meta = subprocess.run(
        ["git", "-C", tmpdir, "log",
         "--format=%H%x1f%an%x1f%ae%x1f%aI%x1f%B%x1e",
         "-n", str(MAX_COMMITS)],
        check=True, timeout=_remaining(deadline),
        capture_output=True, text=True).stdout
    files_out = subprocess.run(
        ["git", "-C", tmpdir, "log", "--format=COMMIT %H", "--name-only",
         "-n", str(MAX_COMMITS)],
        check=True, timeout=_remaining(deadline),
        capture_output=True, text=True).stdout
    records, files_by_sha = {}, {}
    for chunk in meta.split("\x1e"):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        parts = chunk.split("\x1f", 4)
        if len(parts) != 5:
            continue
        sha, name, email, date, body = parts
        title = body.strip().splitlines()[0] if body.strip() else sha[:7]
        records[sha] = {"sha": sha, "name": name, "email": email,
                        "date": date, "title": title, "body": body,
                        "files": []}
    current = None
    for line in files_out.splitlines():
        if line.startswith("COMMIT "):
            current = line.split(" ", 1)[1].strip()
            files_by_sha.setdefault(current, [])
        elif line.strip() and current is not None:
            files_by_sha[current].append(line.strip())
    ordered = []
    for sha, rec in records.items():
        rec["files"] = files_by_sha.get(sha, [])
        ordered.append(rec)
    # `git log` order is newest-first already; keep it.
    return ordered


def _fetch_with_dulwich(url, tmpdir, deadline):
    """Commit records via dulwich (pure Python; used when no git binary).

    Clone with filter_spec="blob:none" (no file contents) + depth 300,
    then walk commits and diff each commit's tree against its first
    parent's tree for the files touched. The clone runs in a worker
    thread so the 90s budget is enforced even though dulwich takes
    no timeout of its own.
    """
    import io
    from dulwich import porcelain
    from dulwich.diff_tree import tree_changes

    # Dulwich resolves a default user identity while cloning, from
    # USER/EMAIL or the GIT_AUTHOR_*/GIT_COMMITTER_* vars. Minimal
    # containers (like Embarko's, running as a user with no passwd
    # entry and no USER var) have none of those, and the clone fails
    # with DefaultIdentityNotFound. WhyCode never commits, so the
    # identity is never used for authorship — these defaults only
    # satisfy the lookup. They are set for the clone call only and
    # restored afterwards, so a later git call in this process (a
    # test fixture, say) still sees its own environment.
    _identity_defaults = (
        ("GIT_AUTHOR_NAME", "WhyCode"),
        ("GIT_AUTHOR_EMAIL", "whycode@localhost"),
        ("GIT_COMMITTER_NAME", "WhyCode"),
        ("GIT_COMMITTER_EMAIL", "whycode@localhost"),
        ("USER", "whycode"),
        ("EMAIL", "whycode@localhost"))
    _saved_env = {k: os.environ.get(k) for k, _ in _identity_defaults}
    for key, value in _identity_defaults:
        os.environ.setdefault(key, value)

    def _clone():
        try:
            return porcelain.clone(
                url, tmpdir, depth=MAX_COMMITS, filter_spec="blob:none",
                errstream=io.BytesIO())
        except Exception:
            # Server may not support partial clone; retry full.
            shutil.rmtree(tmpdir, ignore_errors=True)
            return porcelain.clone(
                url, tmpdir, depth=MAX_COMMITS,
                errstream=io.BytesIO())

    # The clone runs in a worker thread so the 90s budget is enforced
    # even though dulwich takes no timeout of its own. shutdown(wait=
    # False) on timeout: the request thread must not block on a clone
    # that already failed its budget (the abandoned thread just
    # errors out against a tmpdir that is already gone).
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        repo = ex.submit(_clone).result(timeout=_remaining(deadline))
    finally:
        ex.shutdown(wait=False, cancel_futures=True)
        for key, prev in _saved_env.items():
            if prev is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prev
    try:
        records = []
        for entry in repo.get_walker(max_entries=MAX_COMMITS):
            c = entry.commit
            m = re.match(rb"^(.*) <([^<>]*)>$", c.author or b"")
            if m:
                name = m.group(1).decode("utf-8", "replace")
                email = m.group(2).decode("utf-8", "replace")
            else:
                name = (c.author or b"unknown").decode("utf-8", "replace")
                email = ""
            tz = timezone(timedelta(seconds=c.author_timezone or 0))
            date = datetime.fromtimestamp(
                c.author_time or 0, tz=tz).isoformat()
            body = (c.message or b"").decode("utf-8", "replace")
            title = body.strip().splitlines()[0] if body.strip() \
                else c.id.decode()[:7]
            parent = c.parents[0] if c.parents else None
            ptree = repo.object_store[parent].tree if parent else None
            files = []
            for ch in tree_changes(repo.object_store, ptree, c.tree):
                raw = ch.new.path if ch.new is not None else ch.old.path
                path = raw.decode("utf-8", "replace")
                if path not in files:
                    files.append(path)
            records.append({"sha": c.id.decode(), "name": name,
                            "email": email, "date": date, "title": title,
                            "body": body, "files": files})
        return records
    finally:
        repo.close()


def _build_store(records, owner, repo):
    """GraphStore from commit records. Same id scheme as the Django
    graph: commit:<sha>, file:<path>, person:<email|name>; edges
    authored (commit -> person) and touches (commit -> file)."""
    store = GraphStore(":memory:")
    seen_files, seen_people = set(), set()
    for rec in records:
        commit_id = f"commit:{rec['sha']}"
        store.add_entity(
            commit_id, "commit", rec["title"], rec["body"],
            f"https://github.com/{owner}/{repo}/commit/{rec['sha']}",
            rec["date"])
        person_id = (f"person:{rec['email']}" if rec["email"]
                     else f"person:{rec['name']}")
        if person_id not in seen_people:
            seen_people.add(person_id)
            store.add_entity(person_id, "person", rec["name"],
                             rec["email"] or "", "", "")
        store.add_edge(commit_id, person_id, "authored")
        for path in rec["files"]:
            file_id = f"file:{path}"
            if file_id not in seen_files:
                seen_files.add(file_id)
                store.add_entity(
                    file_id, "file", path, "",
                    f"https://github.com/{owner}/{repo}/blob/"
                    f"{rec['sha']}/{quote(path)}", "")
            store.add_edge(commit_id, file_id, "touches")
    return store


def ingest_repo(owner, repo, url=None, timeout=INGEST_TIMEOUT,
                transport=None):
    """Clone a repo's history into its per-repo SQLite graph.

    transport: "git", "dulwich", or None (git CLI when the binary
    exists, dulwich otherwise). Raises IngestError with a
    visitor-friendly message on any failure. Returns stats.
    """
    if (not SEGMENT_RE.match(owner) or not SEGMENT_RE.match(repo)
            or len(owner) > 100 or len(repo) > 100):
        raise IngestError("That repo name doesn't look valid.")
    url = url or f"https://github.com/{owner}/{repo}.git"
    deadline = time.monotonic() + timeout
    if transport == "git":
        if not shutil.which("git"):
            raise IngestError("Ingest needs git on the server, "
                              "which isn't available right now.")
        fetch = _fetch_with_git
    elif transport == "dulwich":
        fetch = _fetch_with_dulwich
    elif shutil.which("git"):
        fetch = _fetch_with_git
    else:
        fetch = _fetch_with_dulwich
    tmpdir = tempfile.mkdtemp(prefix="whycode-clone-")
    try:
        records = fetch(url, tmpdir, deadline)
        if not records:
            raise IngestError(
                "That repo has no commits we could read — is it empty?")
        store = _build_store(records, owner, repo)
        tmp_db = os.path.join(repos_dir(),
                              f".{repo_slug(owner, repo)}.tmp.db")
        if os.path.exists(tmp_db):
            os.remove(tmp_db)
        dest = sqlite3.connect(tmp_db)
        try:
            store.conn.backup(dest)
            n_entities = dest.execute(
                "SELECT COUNT(*) FROM entities").fetchone()[0]
        finally:
            dest.close()
            store.conn.close()
        os.replace(tmp_db, repo_db_path(owner, repo))
        _register(owner, repo, len(records), n_entities)
        return {"owner": owner, "repo": repo, "commits": len(records),
                "entities": n_entities}
    except IngestError:
        raise
    except subprocess.TimeoutExpired:
        raise IngestError(
            "Ingest timed out — that repo is too large to read in "
            f"{timeout} seconds. Try a smaller one.")
    except concurrent.futures.TimeoutError:
        raise IngestError(
            "Ingest timed out — that repo is too large to read in "
            f"{timeout} seconds. Try a smaller one.")
    except subprocess.CalledProcessError:
        raise IngestError(
            "Couldn't read that repo — is it public? Private or "
            "nonexistent repos can't be ingested.")
    except Exception as exc:
        raise IngestError(
            "Couldn't read that repo "
            f"({exc.__class__.__name__}) — is it public?")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
