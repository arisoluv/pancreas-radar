"""Deduplicate, gate for relevance, tag lenses, and score items."""
import re

PANCREAS = re.compile(r"pancrea|pdac", re.I)
# Sources whose queries are broad enough to need a pancreas-relevance gate.
GATED = {"paper", "guideline", "preprint", "trial_new", "grant"}


def dedupe(items):
    seen, out = set(), []
    for it in items:
        doi = (it.get("extra") or {}).get("doi")
        keys = {it["id"], f"doi:{doi.lower()}" if doi else None,
                re.sub(r"\W+", "", it["title"].lower())[:80] or None} - {None}
        if keys & seen:
            continue
        seen |= keys
        out.append(it)
    return out


def relevant(it):
    if it["type"] not in GATED:
        return True  # devices/news are filtered at the source by keyword
    return bool(PANCREAS.search(it["title"]) or PANCREAS.search(it["abstract"][:1500]))


def tag_lenses(it, lenses):
    text = f"{it['title']} {it['abstract']}".lower()
    tags = [name for name, kws in lenses.items() if any(k.lower() in text for k in kws)]
    if it["type"] == "regulatory" and "regulatory" not in tags:
        tags.append("regulatory")
    if it["type"] == "news" and "business" not in tags and "regulatory" not in tags:
        tags.append("business")
    return tags or ["science"]


def journal_key(venue):
    """'The Lancet. Oncology' -> 'lancet. oncology'; 'Gut : journal of ...' -> 'gut'."""
    v = re.split(r" :| \(", (venue or "").lower())[0].strip()
    return v[4:] if v.startswith("the ") else v


def score(it, w):
    extra = it.get("extra") or {}
    s = w["type"].get(it["type"], 0)
    # Best bonus + worst penalty, not a sum: a "Meta-Analysis" is also tagged "Systematic Review" and "Review"
    pts = [w["pubtype"].get(pt, 0) for pt in extra.get("pubtypes", [])]
    s += max([p for p in pts if p > 0], default=0) + min([p for p in pts if p < 0], default=0)
    s += max((w["phase"].get(ph, 0) for ph in extra.get("phases", [])), default=0)
    s += w["journals"].get(journal_key(it.get("venue")), 0)
    text = f"{it['title']} {it['abstract']}".lower()
    s += sum(v for k, v in w["keyword_boost"].items() if k in text)
    if PANCREAS.search(it["title"]):
        s += 2  # pancreas in the title beats a passing mention
    if it["type"] in {"paper", "preprint"} and not it["abstract"]:
        s -= 2  # no abstract: likely a comment or erratum, and nothing to summarize
    return s


def rank(items, cfg):
    items = [it for it in dedupe(items) if relevant(it)]
    for it in items:
        if it["type"] == "paper" and re.match(r"(bio|med)rxiv", it.get("venue") or "", re.I):
            it["type"] = "preprint"  # PubMed indexes some preprints; label them honestly
            it["tags"] = ["Preprint (not peer reviewed)"] + it["tags"]
        it["lenses"] = tag_lenses(it, cfg["lenses"])
        it["score"] = score(it, cfg["weights"])
    return sorted(items, key=lambda it: (it["score"], it["date"]), reverse=True)
