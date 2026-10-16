"""Digest RSS (for the Power Automate -> Teams flow) and events .ics (for Outlook)."""
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape


def digest_rss(digests, site_url):
    """digests: newest-first list of {"week": "YYYY-MM-DD", "top": [items]}."""
    entries = []
    for d in digests[:12]:
        lines = "".join(f"<li><a href=\"{escape(it['url'])}\">{escape(it['title'])}</a> "
                        f"— {escape((it.get('summary') or {}).get('one_liner', it['venue']))}</li>"
                        for it in d["top"])
        pub = datetime.fromisoformat(d["week"]).replace(hour=12, tzinfo=timezone.utc)
        entries.append(f"""  <item>
    <title>Pancreas Radar — week of {d['week']}</title>
    <link>{escape(site_url)}#week-{d['week']}</link>
    <guid isPermaLink="false">pancreas-radar-{d['week']}</guid>
    <pubDate>{format_datetime(pub)}</pubDate>
    <description>{escape('<ol>' + lines + '</ol>')}</description>
  </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Pancreas Radar — weekly digest</title>
  <link>{escape(site_url)}</link>
  <description>Top pancreatic cancer research, trials, regulatory and industry news each week.</description>
{chr(10).join(entries)}
</channel></rss>
"""


def _ics_text(s):
    return str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def events_ics(events):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Pancreas Radar//Events//EN",
           "X-WR-CALNAME:Pancreas Radar events", "CALSCALE:GREGORIAN"]
    for i, e in enumerate(events):
        end = e.get("end") or e["start"]
        # all-day events: DTEND is exclusive, so add one day
        end_excl = datetime.fromordinal(end.toordinal() + 1).date()
        note = f"{e.get('url', '')}" + ("\\n(Dates unverified — check the official site)" if e.get("verify") else "")
        out += ["BEGIN:VEVENT", f"UID:pancreas-radar-{i}-{e['start']:%Y%m%d}@radar", f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{e['start']:%Y%m%d}", f"DTEND;VALUE=DATE:{end_excl:%Y%m%d}",
                f"SUMMARY:{_ics_text(e['name'])}", f"LOCATION:{_ics_text(e.get('location', ''))}",
                f"DESCRIPTION:{note}", "END:VEVENT"]
        if e.get("deadline"):
            out += ["BEGIN:VEVENT", f"UID:pancreas-radar-{i}-deadline@radar", f"DTSTAMP:{stamp}",
                    f"DTSTART;VALUE=DATE:{e['deadline']:%Y%m%d}", f"SUMMARY:Deadline: {_ics_text(e['name'])}",
                    "END:VEVENT"]
    out.append("END:VCALENDAR")
    return "\r\n".join(out) + "\r\n"
