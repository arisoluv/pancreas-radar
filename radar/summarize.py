"""Structured AI summaries, grounded only in the item's abstract.

Uses any OpenAI-compatible chat endpoint, so free tiers can be swapped without code changes:
  GitHub Models (default; in Actions the built-in GITHUB_TOKEN works with `permissions: models: read`)
  Gemini:  LLM_ENDPOINT=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
           LLM_MODEL=gemini-2.5-flash   LLM_API_KEY=<key>
Only public abstracts are ever sent. Never send internal or patient data through this module.
"""
import json
import os
import re
import time

from radar.http import session

# `or`, not a get() default: unset GitHub Actions vars arrive as empty strings
ENDPOINT = os.environ.get("LLM_ENDPOINT") or "https://models.github.ai/inference/chat/completions"
MODEL = os.environ.get("LLM_MODEL") or "openai/gpt-4o-mini"

PROMPT = """You summarize pancreatic cancer research for a multidisciplinary team
(clinical, science, regulatory, business, strategy). Use ONLY the text provided. Do not add outside facts.
Return JSON with exactly these keys:
  "one_liner": plain-language sentence (<= 30 words) of what was found or announced,
  "design": study design / item type in <= 12 words (e.g. "Phase 3 RCT", "Retrospective cohort", "510(k) clearance"),
  "population": who/what and sample size if stated, else "",
  "key_results": up to 4 objects {"label": short metric name, "value": the number(s) as written,
                  "quote": the EXACT sentence fragment from the text containing that number},
  "so_what": object with any of keys clinical, science, regulatory, business, strategic -> one sentence each,
             only for lenses where the text supports an implication,
  "caveats": one sentence on limitations visible in the text, or "".
If the text has no numbers, return key_results as []."""


def _norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def _grounded(summary, source):
    """Drop any key result whose quote isn't literally in the source text."""
    src = _norm(source)
    kept = [r for r in summary.get("key_results", [])
            if r.get("quote") and _norm(r["quote"]) in src and str(r.get("value", "")).strip()]
    summary["dropped_unverified"] = len(summary.get("key_results", [])) - len(kept)
    summary["key_results"] = kept
    return summary


def summarize(items, n):
    key = os.environ.get("LLM_API_KEY") or os.environ.get("GITHUB_TOKEN")
    if not key or n <= 0:
        print("  (summaries skipped: no LLM_API_KEY/GITHUB_TOKEN)")
        return
    s = session()
    for it in [i for i in items if i["abstract"]][:n]:
        source = f"TITLE: {it['title']}\nSOURCE: {it['venue']}\nTEXT: {it['abstract']}"
        try:
            r = s.post(ENDPOINT, headers={"Authorization": f"Bearer {key}"}, timeout=90, json={
                "model": MODEL, "temperature": 0.1, "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": PROMPT}, {"role": "user", "content": source}]})
            r.raise_for_status()
            if "json" not in r.headers.get("Content-Type", ""):
                raise ValueError(f"non-JSON reply from {ENDPOINT} (proxy or wrong endpoint?): {r.text[:80]!r}")
            it["summary"] = _grounded(json.loads(r.json()["choices"][0]["message"]["content"]), source)
        except Exception as e:  # a failed summary must not fail the run
            print(f"  ! summary {it['id']}: {str(e)[:150]}")
        time.sleep(4)  # free tiers are rate limited per minute
