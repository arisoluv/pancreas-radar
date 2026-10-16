"""Newly registered trials via ClinicalTrials.gov API v2."""
from radar.http import session

URL = "https://clinicaltrials.gov/api/v2/studies"


def fetch(cfg, since, until):
    r = session().get(URL, params={
        "query.cond": cfg["condition"],
        "filter.advanced": f"AREA[StudyFirstPostDate]RANGE[{since},{until}]",
        "pageSize": cfg.get("max_results", 100), "format": "json"}, timeout=60)
    r.raise_for_status()
    items = []
    for st in r.json().get("studies", []):
        p = st.get("protocolSection", {})
        ident, status = p.get("identificationModule", {}), p.get("statusModule", {})
        design, sponsor = p.get("designModule", {}), p.get("sponsorCollaboratorsModule", {})
        lead = sponsor.get("leadSponsor") or {}
        nct = ident.get("nctId")
        phases = design.get("phases") or []
        interventions = [i.get("name") for i in p.get("armsInterventionsModule", {}).get("interventions", [])]
        items.append({
            "id": f"nct:{nct}", "source": "ClinicalTrials.gov", "type": "trial_new",
            "title": ident.get("briefTitle", ""), "url": f"https://clinicaltrials.gov/study/{nct}",
            "date": (status.get("studyFirstPostDateStruct") or {}).get("date", ""),
            "abstract": (p.get("descriptionModule") or {}).get("briefSummary", ""),
            "venue": lead.get("name", ""),
            "tags": phases + [status.get("overallStatus", "")],
            "extra": {"nct": nct, "phases": phases, "status": status.get("overallStatus"),
                      "enrollment": (design.get("enrollmentInfo") or {}).get("count"),
                      "sponsor_class": lead.get("class"), "interventions": interventions},
        })
    return items
