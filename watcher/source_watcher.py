"""Source watcher: keeps Shotclock's library current without anyone re-downloading by hand.

Every file in docs/ starts with its official source URL and a "Checked:" date. This script:
  1. finds those URLs,
  2. downloads each document and fingerprints it (SHA-256),
  3. compares with the last fingerprint a person approved (watcher/manifest.json),
  4. checks watchlist.json for known documents that are not in the library yet.

It never edits docs/. A person reviews what changed, updates the file, and approves the new baseline
(human in the loop: this is legal information).

    python watcher/source_watcher.py            # check and print a report
    python watcher/source_watcher.py --approve  # also save current fingerprints as the approved baseline
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MANIFEST = Path(__file__).resolve().parent / "manifest.json"
WATCHLIST = Path(__file__).resolve().parent / "watchlist.json"
USER_AGENT = "Shotclock-source-watcher/0.1 (hackathon prototype)"
STALE_DAYS = 180
HEADER_LINES = 12  # source URLs and "Checked:" live at the top of each file

URL_RE = re.compile(r"https?://[^\s)>\]\"']+")
CHECKED_RE = re.compile(r"(?:Checked|verified)[^0-9]{0,20}(\d{4}-\d{2}-\d{2})", re.I)


@dataclass
class Source:
    file: str  # docs/... path
    title: str
    urls: list[str]
    checked: str | None  # YYYY-MM-DD from the file header, if stated


@dataclass
class Check:
    url: str
    files: list[str] = field(default_factory=list)
    status: str = ""  # unchanged | changed | new | online | moved | unreachable
    http: int | None = None
    final_url: str | None = None
    sha256: str | None = None
    size: int | None = None
    content_type: str | None = None
    last_modified: str | None = None
    note: str = ""


def find_sources() -> list[Source]:
    out = []
    for p in sorted(DOCS.rglob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        head = p.read_text(errors="ignore").splitlines()[:HEADER_LINES]
        text = "\n".join(head)
        urls = list(dict.fromkeys(u.rstrip(".,;:") for u in URL_RE.findall(text)))
        m = CHECKED_RE.search(text)
        title = next((ln.lstrip("# ").strip() for ln in head if ln.strip()), p.name)
        out.append(Source(str(p.relative_to(ROOT)), title, urls, m.group(1) if m else None))
    return out


def fetch(url: str, timeout: int = 25) -> Check:
    c = Check(url=url)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            c.http = r.status
            c.final_url = r.geturl()
            c.content_type = (r.headers.get("Content-Type") or "").split(";")[0]
            c.last_modified = r.headers.get("Last-Modified")
    except urllib.error.HTTPError as e:
        c.http, c.status = e.code, "unreachable"
        c.note = (f"HTTP {e.code}: site blocks automated checks; check it in a browser" if e.code in (401, 403, 429)
                  else f"HTTP {e.code}: link is dead or moved; find the new link")
        return c
    except Exception as e:  # DNS, timeout, TLS
        c.status, c.note = "unreachable", type(e).__name__
        return c
    c.sha256 = hashlib.sha256(body).hexdigest()
    c.size = len(body)
    if c.content_type == "text/html" and url.lower().endswith(".pdf"):
        c.status, c.note = "unreachable", "expected a PDF, got a web page (likely an error page)"
    return c


def fetch_politely(urls: list[str]) -> dict[str, Check]:
    """Different sites in parallel, but one request at a time per site, with a pause and one retry.
    (Event rule: don't overload city websites. San Clemente's site also refuses bursts.)"""
    by_host: dict[str, list[str]] = {}
    for u in urls:
        by_host.setdefault(urlparse(u).netloc, []).append(u)

    def one_host(host_urls: list[str]) -> list[tuple[str, Check]]:
        out = []
        for i, u in enumerate(host_urls):
            if i:
                time.sleep(1)
            c = fetch(u)
            if c.status == "unreachable" and c.http not in (403, 404, 410):
                time.sleep(3)
                c = fetch(u)
            out.append((u, c))
        return out

    with ThreadPoolExecutor(max_workers=len(by_host) or 1) as ex:
        return {u: c for chunk in ex.map(one_host, by_host.values()) for u, c in chunk}


def load_json(p: Path, default):
    try:
        return json.loads(p.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def run(approve: bool = False, pretend_changed: str | None = None) -> dict:
    """pretend_changed: a URL to treat as changed (demo only; nothing is written)."""
    sources = find_sources()
    by_url: dict[str, list[str]] = {}
    for s in sources:
        for u in s.urls:
            by_url.setdefault(u, []).append(s.file)
    watch = load_json(WATCHLIST, {"items": []})["items"]
    manifest = load_json(MANIFEST, {})

    urls = list(by_url) + [w["url"] for w in watch if w["url"] not in by_url]
    results = fetch_politely(urls)

    checks = []
    for u, files in by_url.items():
        c = results[u]
        c.files = files
        if c.status != "unreachable":
            old = manifest.get(u)
            if c.final_url and urlparse(c.final_url).netloc != urlparse(u).netloc:
                c.status, c.note = "moved", f"redirects to {c.final_url}"
            elif c.content_type == "text/html":
                c.status, c.note = "online", "web page: checked that it is still up (its content varies on every load)"
            elif not old:
                c.status, c.note = "new", "no approved fingerprint yet"
            elif old["sha256"] == c.sha256 and u != pretend_changed:
                c.status = "unchanged"
            else:
                c.status = "changed"
                c.note = f"was {old.get('size')} bytes (approved {old.get('approved')}), now {c.size} bytes"
                if u == pretend_changed:
                    c.note = "DEMO: simulated change. A person would now review the new version and update docs/"
        checks.append(c)

    candidates = []
    for w in watch:
        c = results[w["url"]]
        loaded = w["url"] in by_url
        candidates.append({**w, "reachable": c.status != "unreachable", "http": c.http,
                           "note": c.note, "in_library": loaded})

    today = date.today()
    if approve:
        for c in checks:
            if c.sha256 and c.status in ("new", "changed", "unchanged") and c.content_type != "text/html":
                manifest[c.url] = {"sha256": c.sha256, "size": c.size, "last_modified": c.last_modified,
                                   "approved": today.isoformat()}
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    # Freshness: the newer of the file's own "Checked:" date and the date a person approved its fingerprint.
    freshness = []
    for s in sources:
        dates = [s.checked] if s.checked else []
        dates += [manifest[u]["approved"] for u in s.urls if u in manifest]
        last = max(dates) if dates else None
        age = (today - datetime.strptime(last, "%Y-%m-%d").date()).days if last else None
        freshness.append({**asdict(s), "last_verified": last, "age_days": age,
                          "stale": age is None or age > STALE_DAYS})

    return {"run_at": datetime.now().isoformat(timespec="seconds"), "checks": [asdict(c) for c in checks],
            "candidates": candidates, "freshness": freshness, "approved": approve}


ICON = {"online": "🌐", "unchanged": "✅", "changed": "🆕", "new": "🔵", "moved": "↪️", "unreachable": "⚠️"}


def print_report(rep: dict) -> None:
    print(f"Shotclock source watcher · {rep['run_at']}\n")
    print("Library sources")
    for c in rep["checks"]:
        files = ", ".join(Path(f).name for f in c["files"])
        print(f"  {ICON.get(c['status'], '?')} {c['status']:<11} {c['url']}\n      used by: {files}"
              + (f"\n      {c['note']}" if c["note"] else ""))
    print("\nWatchlist (known documents not yet in the library)")
    for w in rep["candidates"]:
        mark = "already loaded" if w["in_library"] else ("available → review and add" if w["reachable"]
                                                          else f"not reachable ({w['note']})")
        print(f"  • {w['name']}: {mark}\n      {w['url']}")
    stale = [f for f in rep["freshness"] if f["stale"]]
    print(f"\nFreshness: {len(rep['freshness']) - len(stale)} of {len(rep['freshness'])} files checked "
          f"within {STALE_DAYS} days")
    for f in stale:
        print(f"  ⚠️ {f['file']}: " + (f"last verified {f['age_days']} days ago" if f["last_verified"]
                                      else "never verified (no 'Checked:' date, no approved fingerprint)"))
    if rep["approved"]:
        print(f"\nApproved: current fingerprints saved to {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    print_report(run(approve="--approve" in sys.argv))
