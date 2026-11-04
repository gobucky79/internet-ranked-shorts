"""Phone notifications for the creator, sent as GitHub issues on this repo.

GitHub emails the repo owner and pings the GitHub mobile app for every issue that @mentions them, so an issue is a
free, no-setup push notification. Each alert carries a short `key` in its title (e.g. "[short:babies_lemon]") so the
bots never open the same alert twice and can close it again when it's resolved.

Needs GITHUB_TOKEN and GITHUB_REPOSITORY (set automatically in GitHub Actions; the workflow must grant
`issues: write`). Outside Actions, alerts are just printed.
"""
import os

import requests

API = "https://api.github.com"


def _ctx():
    tok, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    return (tok, repo) if tok and repo else (None, None)


def _h(tok):
    return {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}


def _owner():
    return os.environ.get("GITHUB_REPOSITORY_OWNER") or (os.environ.get("GITHUB_REPOSITORY", "/").split("/")[0])


def find_open(key):
    """Open issue whose title contains [key], or None."""
    tok, repo = _ctx()
    if not tok:
        return None
    r = requests.get(f"{API}/repos/{repo}/issues", headers=_h(tok),
                     params={"state": "open", "per_page": 100}, timeout=30)
    r.raise_for_status()
    tag = f"[{key}]"
    for i in r.json():
        if tag in i["title"] and "pull_request" not in i:
            return i
    return None


def alert(key, title, body, urgent=False):
    """Open an issue (once per key) that pings the creator. Returns the issue number or None."""
    full_title = f"{'🚨 ' if urgent else ''}{title} [{key}]"
    body = f"@{_owner()}\n\n{body}"
    tok, repo = _ctx()
    if not tok:
        print(f"ALERT (not sent, no GitHub token): {full_title}\n{body}")
        return None
    try:
        existing = find_open(key)
        if existing:
            return existing["number"]
        r = requests.post(f"{API}/repos/{repo}/issues", headers=_h(tok),
                          json={"title": full_title, "body": body}, timeout=30)
        r.raise_for_status()
        n = r.json()["number"]
        print(f"alert sent: #{n} {full_title}")
        return n
    except requests.RequestException as e:          # a failed alert must never stop the pipeline
        print(f"could not send alert ({e}): {full_title}")
        return None


def resolve(key, comment=None):
    """Close the open alert for key (if any), optionally leaving a comment."""
    tok, repo = _ctx()
    if not tok:
        return
    try:
        i = find_open(key)
        if not i:
            return
        if comment:
            requests.post(f"{API}/repos/{repo}/issues/{i['number']}/comments", headers=_h(tok),
                          json={"body": comment}, timeout=30)
        requests.patch(f"{API}/repos/{repo}/issues/{i['number']}", headers=_h(tok),
                       json={"state": "closed"}, timeout=30)
    except requests.RequestException as e:
        print(f"could not close alert {key}: {e}")
