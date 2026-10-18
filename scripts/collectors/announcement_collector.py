"""Collect protein-design announcements that have no repository.

A result can land as a blog post, a preprint or a release note long before any
code exists — or instead of code existing at all. Those entries have no stars
to rank by, so they are collected here and kept in their own file with their
own schema, rather than forced into repos.json.

Standard library only: the daily workflow should not gain a dependency for
reading RSS.
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = ROOT / "data" / "announcements.json"
LOG_DIR = ROOT / "data" / "run_logs"
CONFIG_PATH = ROOT / "config.json"

USER_AGENT = "FoldScape/1.0 (+https://boemartinez.github.io/FoldScape)"

# Verified reachable 2026-10-17. Each entry is (name, url).
DEFAULT_FEEDS = [
    ("bioRxiv Bioinformatics", "https://connect.biorxiv.org/biorxiv_xml.php?subject=bioinformatics"),
    ("bioRxiv Biochemistry", "https://connect.biorxiv.org/biorxiv_xml.php?subject=biochemistry"),
    ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
    ("Google AI Blog", "https://blog.google/technology/ai/rss/"),
    ("UW Institute for Protein Design", "https://www.ipd.uw.edu/feed/"),
    ("arXiv q-bio.BM", "https://rss.arxiv.org/rss/q-bio.BM"),
]

# Any one of these is enough on its own.
STRONG = {
    "protein design", "protein engineering", "binder", "de novo protein",
    "alphafold", "rosetta", "proteinmpnn", "rfdiffusion", "esmfold", "boltz",
    "protein language model", "inverse folding", "structure prediction",
    "antibody design", "nanobody", "enzyme design", "protein structure",
    "folding", "peptide design", "molecular dynamics", "cryo-em structure",
}

# Only count when two or more appear together.
WEAK = {
    "protein", "enzyme", "antibody", "peptide", "sequence", "residue",
    "binding affinity", "crystal structure", "amino acid", "proteome",
    "docking", "ligand", "epitope", "catalytic",
}

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

ATOM = "{http://www.w3.org/2005/Atom}"


def load_feeds():
    """Feeds come from config.json when present, so sources are data not code."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            configured = json.load(fh).get("announcements", {}).get("feeds")
    except (OSError, json.JSONDecodeError):
        configured = None

    if not configured:
        return list(DEFAULT_FEEDS)
    return [(f["name"], f["url"]) for f in configured]


def clean(text):
    """Strip markup and collapse whitespace."""
    if not text:
        return ""
    return WS_RE.sub(" ", TAG_RE.sub(" ", text)).strip()


def is_relevant(haystack):
    """A strong signal is required.

    An earlier version also accepted two weak terms together. Measured against
    one day of bioRxiv that let in half again as many entries, all of them
    general bioinformatics — a cucurbit multi-omics agent, a neoantigen
    database. Weak terms are kept only to record why something matched.
    """
    low = haystack.lower()
    hits = [s for s in STRONG if s in low]
    if not hits:
        return False, []
    return True, hits + [w for w in WEAK if w in low]


def parse_date(raw):
    """RSS uses RFC 822, Atom uses ISO 8601. Return ISO 8601 or None."""
    if not raw:
        return None
    raw = raw.strip()
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except ValueError:
        return None


def fetch(url, timeout=30):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def local(tag):
    """Tag name without its namespace. bioRxiv publishes RSS 1.0, where every
    element is namespaced, so matching on a bare tag name finds nothing."""
    return tag.rsplit("}", 1)[-1]


def child_text(node, *names):
    """First matching child's text, ignoring namespaces."""
    for child in node:
        if local(child.tag) in names:
            if child.text and child.text.strip():
                return child.text
    return ""


def entry_link(node):
    """RSS puts the URL in <link> text; Atom puts it in a link element's href."""
    for child in node:
        if local(child.tag) != "link":
            continue
        href = child.get("href")
        if href and child.get("rel", "alternate") == "alternate":
            return href.strip()
        if child.text and child.text.strip():
            return child.text.strip()
    return ""


def parse_feed(raw, source):
    """Read RSS 2.0, RSS 1.0 (RDF) and Atom with one parser."""
    root = ElementTree.fromstring(raw)
    records = []

    for node in root.iter():
        if local(node.tag) not in ("item", "entry"):
            continue
        title = clean(child_text(node, "title"))
        link = entry_link(node)
        summary = clean(child_text(node, "description", "summary", "content", "encoded"))
        published = parse_date(child_text(node, "pubDate", "published", "updated", "date"))
        if link and title:
            records.append((title, link, summary, published))
    return records


def collect():
    feeds = load_feeds()
    now = datetime.now(timezone.utc).isoformat()

    existing = {}
    if OUT_PATH.exists():
        with open(OUT_PATH, "r", encoding="utf-8") as fh:
            for rec in json.load(fh):
                existing[rec["url"]] = rec

    per_feed = {}
    failures = {}
    found = []

    for name, url in feeds:
        try:
            raw = fetch(url)
            entries = parse_feed(raw, name)
        except (HTTPError, URLError, ElementTree.ParseError, OSError) as err:
            failures[name] = f"{type(err).__name__}: {err}"
            per_feed[name] = {"entries": 0, "kept": 0, "error": failures[name]}
            print(f"  {name}: FAILED - {failures[name]}")
            continue

        kept = 0
        for title, link, summary, published in entries:
            relevant, matched = is_relevant(f"{title} {summary}")
            if not relevant:
                continue
            kept += 1
            found.append({
                "url": link,
                "title": title,
                "source": name,
                "summary": summary[:600],
                "published": published,
                "matched": sorted(matched)[:6],
            })

        per_feed[name] = {"entries": len(entries), "kept": kept}
        print(f"  {name}: {len(entries)} entries, {kept} relevant")
        time.sleep(0.5)

    # Every feed down is a broken collector, not a quiet day. Say so loudly.
    if failures and len(failures) == len(feeds):
        print(f"\nAll {len(feeds)} feeds failed. Not writing output.", file=sys.stderr)
        write_log(per_feed, 0, 0, len(existing), failures)
        return 1

    added = 0
    for rec in found:
        prior = existing.get(rec["url"])
        if prior:
            prior.update({k: rec[k] for k in ("title", "summary", "published", "matched")})
            prior["last_seen"] = now
        else:
            rec["first_seen"] = now
            rec["last_seen"] = now
            existing[rec["url"]] = rec
            added += 1

    records = sorted(
        existing.values(),
        key=lambda r: (r.get("published") or r.get("first_seen") or ""),
        reverse=True,
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)

    print(f"\n{len(records)} announcements on file ({added} new this run)")
    print(f"Written to {OUT_PATH}")
    write_log(per_feed, len(found), added, len(records), failures)
    return 0


def write_log(per_feed, relevant, added, total, failures):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "announcements",
        "feeds": per_feed,
        "relevant_this_run": relevant,
        "new": added,
        "total_after": total,
        "failed_feeds": failures,
    }
    path = LOG_DIR / f"announcements_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=2)
    print(f"Run log saved to {path}")


if __name__ == "__main__":
    print("Starting announcement collection...")
    sys.exit(collect())
