"""Preprints (bioRxiv, medRxiv, Research Square, ...) via Europe PMC REST API."""
from radar.http import session

URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def fetch(cfg, since, until):
    q = f'{cfg["query"]} AND SRC:PPR AND FIRST_PDATE:[{since} TO {until}]'
    r = session().get(URL, params={"query": q, "format": "json", "resultType": "core",
                                   "pageSize": cfg.get("max_results", 100)}, timeout=60)
    r.raise_for_status()
    items = []
    for d in r.json().get("resultList", {}).get("result", []):
        doi = d.get("doi")
        items.append({
            "id": f"doi:{doi.lower()}" if doi else f"ppr:{d['id']}",
            "source": "Europe PMC", "type": "preprint",
            "title": (d.get("title") or "").strip(),
            "url": f"https://doi.org/{doi}" if doi else f"https://europepmc.org/article/PPR/{d['id']}",
            "date": d.get("firstPublicationDate", ""), "abstract": d.get("abstractText") or "",
            "venue": (d.get("bookOrReportDetails") or {}).get("publisher", "Preprint"),
            "tags": ["Preprint (not peer reviewed)"], "extra": {"doi": doi},
        })
    return items
