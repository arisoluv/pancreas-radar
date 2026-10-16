"""Entry point: collect -> rank -> summarize -> publish.

  python -m radar.run              # full run, writes docs/ and data/
  python -m radar.run --dry-run    # collect + rank only, print a report, write nothing
"""
import argparse
import importlib
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from radar import feeds
from radar.rank import rank
from radar.summarize import summarize

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [  # (module, config key, lookback key)
    ("pubmed", "pubmed", "lookback_days"),
    ("europepmc", "europepmc_preprints", "lookback_days"),
    ("ctgov", "clinicaltrials", "lookback_days"),
    ("openfda", "openfda_devices", "lookback_days"),
    ("reporter", "nih_reporter", "grants_lookback_days"),
    ("rss", "rss", "lookback_days"),
]


def collect(cfg, until):
    items, ok = [], []
    for mod, key, lb in SOURCES:
        scfg = cfg["sources"].get(key, {})
        if not scfg.get("enabled"):
            continue
        since = until - timedelta(days=cfg[lb])
        try:
            got = importlib.import_module(f"radar.sources.{mod}").fetch(scfg, since, until)
            print(f"  {mod:10s} {len(got):4d}")
            items += got
            ok.append(mod)
        except Exception as e:  # a broken source is reported, not fatal
            print(f"  {mod:10s} FAILED: {str(e)[:200]}")
    return items, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--until", help="end date YYYY-MM-DD (default today)")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config/queries.yaml").read_text(encoding="utf-8"))
    events = yaml.safe_load((ROOT / "config/events.yaml").read_text(encoding="utf-8"))["events"] or []
    until = date.fromisoformat(args.until) if args.until else date.today()
    since = until - timedelta(days=cfg["lookback_days"])

    print("Collecting…")
    raw, ok = collect(cfg, until)
    items = rank(raw, cfg)
    print(f"Kept {len(items)} of {len(raw)} after dedupe + relevance gate.")

    if args.dry_run:
        for it in items[:15]:
            print(f"  {it['score']:3d}  {it['type']:10s} {','.join(it['lenses']):28s} {it['title'][:70]}")
        return

    print("Summarizing…")
    summarize([i for i in items if i["type"] != "trial_new"], cfg["summarize_top"])

    data_dir, docs = ROOT / "data", ROOT / "docs"
    data_dir.mkdir(exist_ok=True)
    docs.mkdir(exist_ok=True)
    payload = {
        "since": str(since), "until": str(until), "top_n": cfg["top_n"], "sources": ok, "items": items,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "events": [{k: str(v) if isinstance(v, date) else v for k, v in e.items()} for e in events],
        "podcast": (docs / "podcast.xml").exists(),
    }
    (data_dir / f"{until}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    html = (ROOT / "radar/site_template.html").read_text(encoding="utf-8")
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    (docs / "index.html").write_text(html.replace("/*__DATA__*/null", blob), encoding="utf-8")

    site_url = os.environ.get("SITE_URL", "https://example.github.io/pancreas-radar/")
    digests = []
    for f in sorted(data_dir.glob("*.json"), reverse=True)[:12]:
        d = json.loads(f.read_text(encoding="utf-8"))
        digests.append({"week": d["until"], "top": [i for i in d["items"] if i["type"] != "trial_new"][:d["top_n"]]})
    (docs / "digest.xml").write_text(feeds.digest_rss(digests, site_url), encoding="utf-8")
    (docs / "events.ics").write_text(feeds.events_ics(events), encoding="utf-8", newline="")
    print(f"Wrote docs/index.html, docs/digest.xml, docs/events.ics, data/{until}.json")


if __name__ == "__main__":
    main()
