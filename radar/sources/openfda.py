"""FDA device decisions (510(k) and PMA) via openFDA. Free; set OPENFDA_API_KEY for higher limits."""
import os

from radar.http import session


def _query(endpoint, name_field, terms, since, until):
    names = " OR ".join(f'{name_field}:"{t}"' for t in terms)
    params = {"search": f"decision_date:[{since:%Y%m%d} TO {until:%Y%m%d}] AND ({names})", "limit": 100}
    if os.environ.get("OPENFDA_API_KEY"):
        params["api_key"] = os.environ["OPENFDA_API_KEY"]
    r = session().get(f"https://api.fda.gov/device/{endpoint}.json", params=params, timeout=60)
    if r.status_code == 404:  # openFDA answers "no matches" with 404
        return []
    r.raise_for_status()
    return r.json().get("results", [])


def _iso(d):
    if d and len(d) == 8 and d.isdigit():
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return d or ""


def fetch(cfg, since, until):
    terms, items = cfg["device_terms"], []
    for d in _query("510k", "device_name", terms, since, until):
        k = d.get("k_number")
        items.append({
            "id": f"510k:{k}", "source": "FDA 510(k)", "type": "regulatory",
            "title": f"510(k) cleared: {d.get('device_name', '')} ({d.get('applicant', '')})",
            "url": f"https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID={k}",
            "date": _iso(d.get("decision_date")), "abstract": "", "venue": d.get("applicant", ""),
            "tags": ["Device", "510(k)", d.get("advisory_committee_description", "")],
            "extra": {"product_code": d.get("product_code")},
        })
    for d in _query("pma", "trade_name", terms, since, until):
        pma = d.get("pma_number", "") + d.get("supplement_number", "")
        items.append({
            "id": f"pma:{pma}", "source": "FDA PMA", "type": "regulatory",
            "title": f"PMA decision: {d.get('trade_name', '')} ({d.get('applicant', '')})",
            "url": f"https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpma/pma.cfm?id={pma}",
            "date": _iso(d.get("decision_date")), "abstract": d.get("ao_statement") or "",
            "venue": d.get("applicant", ""), "tags": ["Device", "PMA"], "extra": {},
        })
    return items
