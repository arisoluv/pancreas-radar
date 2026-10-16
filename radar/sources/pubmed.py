"""PubMed via NCBI E-utilities (free; set NCBI_API_KEY for higher rate limits)."""
import os
import time
import xml.etree.ElementTree as ET

from radar.http import session

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def _params(**kw):
    if os.environ.get("NCBI_API_KEY"):
        kw["api_key"] = os.environ["NCBI_API_KEY"]
    kw.setdefault("tool", "pancreas-radar")
    return kw


def _date(art):
    for status in ("pubmed", "entrez"):
        d = art.find(f"PubmedData/History/PubMedPubDate[@PubStatus='{status}']")
        if d is not None:
            y, m, dd = (d.findtext(k, "1") for k in ("Year", "Month", "Day"))
            return f"{int(y):04d}-{int(m):02d}-{int(dd):02d}"
    return ""


def fetch(cfg, since, until):
    s = session()
    r = s.get(BASE + "esearch.fcgi", params=_params(
        db="pubmed", term=cfg["term"], datetype="edat", mindate=since.strftime("%Y/%m/%d"),
        maxdate=until.strftime("%Y/%m/%d"), retmax=cfg.get("max_results", 300), retmode="json"), timeout=30)
    r.raise_for_status()
    ids = r.json()["esearchresult"]["idlist"]
    items = []
    for i in range(0, len(ids), 100):
        time.sleep(0.4)  # stay under 3 req/s without an API key
        r = s.post(BASE + "efetch.fcgi", data=_params(db="pubmed", id=",".join(ids[i:i + 100]), retmode="xml"),
                   timeout=60)
        r.raise_for_status()
        for art in ET.fromstring(r.content).findall("PubmedArticle"):
            pmid = art.findtext("MedlineCitation/PMID")
            a = art.find("MedlineCitation/Article")
            title = "".join(a.find("ArticleTitle").itertext()).strip()
            abstract = "\n".join(
                ((p.get("Label") + ": ") if p.get("Label") else "") + "".join(p.itertext()).strip()
                for p in a.findall("Abstract/AbstractText"))
            pubtypes = [p.text for p in a.findall("PublicationTypeList/PublicationType") if p.text]
            doi = next((e.text for e in art.findall("PubmedData/ArticleIdList/ArticleId")
                        if e.get("IdType") == "doi"), None)
            items.append({
                "id": f"pmid:{pmid}", "source": "PubMed",
                "type": "guideline" if any("Guideline" in p for p in pubtypes) else "paper",
                "title": title, "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "date": _date(art), "abstract": abstract,
                "venue": a.findtext("Journal/Title", ""), "tags": pubtypes,
                "extra": {"doi": doi, "pubtypes": pubtypes},
            })
    return items
