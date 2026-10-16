"""Curated news RSS feeds. Keeps headline + link + short publisher snippet only (no full text)."""
import hashlib
import re
from datetime import date

import feedparser

from radar.http import session


def fetch(cfg, since, until):
    keys = [k.lower() for k in cfg.get("rss_filter", [])]
    s, items = session(), []
    for feed in cfg["feeds"]:
        try:
            r = s.get(feed["url"], timeout=30)
            r.raise_for_status()
        except Exception as e:  # one dead feed must not kill the run
            print(f"  ! rss {feed['name']}: {e}")
            continue
        for e in feedparser.parse(r.content).entries:
            t = e.get("published_parsed") or e.get("updated_parsed")
            d = date(*t[:3]) if t else until
            if not since <= d <= until:
                continue
            title = e.get("title", "").strip()
            snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", e.get("summary") or "")).strip()[:400]
            if keys and not any(k in f"{title} {snippet}".lower() for k in keys):
                continue
            items.append({
                "id": "rss:" + hashlib.sha1(title.lower().encode()).hexdigest()[:16],
                "source": feed["name"], "type": "regulatory" if "fda" in feed["name"].lower() else "news",
                "title": title, "url": e.get("link", ""), "date": d.isoformat(), "abstract": snippet,
                "venue": feed["name"], "tags": ["News"], "extra": {},
            })
    return items
