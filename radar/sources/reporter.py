"""Newly awarded NIH grants via NIH RePORTER API v2."""
from radar.http import session

URL = "https://api.reporter.nih.gov/v2/projects/search"


def fetch(cfg, since, until):
    body = {
        "criteria": {
            "advanced_text_search": {"operator": "and", "search_field": "projecttitle,terms",
                                     "search_text": cfg["text"]},
            "award_notice_date": {"from_date": str(since), "to_date": str(until)},
        },
        "include_fields": ["ApplId", "ProjectTitle", "Organization", "AwardAmount", "ContactPiName",
                           "AwardNoticeDate", "AbstractText", "AgencyIcAdmin", "ActivityCode"],
        "limit": 100, "offset": 0,
    }
    r = session().post(URL, json=body, timeout=60)
    r.raise_for_status()
    items = []
    for p in r.json().get("results", []):
        items.append({
            "id": f"nih:{p['appl_id']}", "source": "NIH RePORTER", "type": "grant",
            "title": p.get("project_title", ""), "url": f"https://reporter.nih.gov/project-details/{p['appl_id']}",
            "date": (p.get("award_notice_date") or "")[:10], "abstract": p.get("abstract_text") or "",
            "venue": (p.get("organization") or {}).get("org_name", ""), "tags": [p.get("activity_code") or ""],
            "extra": {"award": p.get("award_amount"), "pi": p.get("contact_pi_name"),
                      "ic": (p.get("agency_ic_admin") or {}).get("abbreviation")},
        })
    return items
