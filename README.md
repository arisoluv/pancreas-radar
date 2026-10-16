# Pancreas Radar

A weekly digest of pancreatic cancer research, new trials, FDA device decisions, NIH grants, industry news and events. Each item is tagged with one or more of five lenses (clinical, science, regulatory, business, strategic). It costs $0 to run: GitHub Actions + GitHub Pages + Microsoft 365 standard connectors.

**For teammates:** you don't need to install anything.
1. Open the Teams channel tab (or the site link).
2. Pick a lens.
3. Optionally, subscribe to the events calendar in Outlook: *Add calendar → From internet →* `<site>/events.ics`.

## What it collects (all free, official APIs)
| Source | What | Window |
|---|---|---|
| PubMed (E-utilities) | Papers, guidelines | 7 days |
| Europe PMC | Preprints (bioRxiv, medRxiv, …), labeled "not peer reviewed" | 7 days |
| ClinicalTrials.gov v2 | Newly registered trials | 7 days |
| openFDA | 510(k)/PMA device decisions, using the device terms in config | 7 days |
| NIH RePORTER | New awards | 30 days |
| RSS | FDA press releases, MedTech Dive, Google News searches (headline + link only) | 7 days |

Items are deduplicated, kept only if they're about the pancreas, tagged by lens and scored. Scoring uses study type, trial phase, journal and keywords; edit the weights in `config/queries.yaml`.

**AI summaries:**
- Only the top items get one, and each is built only from the item's public abstract.
- Each key number must come with a quote, and that quote must appear word for word in the abstract. Numbers whose quote doesn't match are removed.
- Never put internal, unpublished or patient data through this pipeline. Free AI tiers may train on inputs.

## Run it on your computer
```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # macOS/Linux: .venv/bin/pip
.venv/Scripts/python -m radar.run --dry-run    # collect + rank, print the top 15, write nothing
.venv/Scripts/python -m radar.run              # writes docs/index.html, digest.xml, events.ics, data/<date>.json
```

## Deploy (one time, about 20 min)
1. Optional: claim the free GitHub Student Developer Pack, which gives you GitHub Pro.
2. Create a GitHub repo and push this folder. `private/` is git-ignored.
3. Repo **Settings → Pages**: Source = *Deploy from a branch*, Branch = `main`, folder `/docs`.
4. Repo **Settings → Actions → General**: Workflow permissions = *Read and write*.
5. **Actions → Weekly radar → Run workflow** to test. After that it runs every Monday.
6. Optional repo secrets: `NCBI_API_KEY` (free, NCBI account) and `OPENFDA_API_KEY` (free). AI summaries use the built-in `GITHUB_TOKEN` with GitHub Models. To use another free provider instead, set the `LLM_API_KEY` secret and the `LLM_ENDPOINT` / `LLM_MODEL` variables (see `radar/summarize.py`).

> The Pages site is reachable by anyone who has the link. That's fine for public abstracts. Team discussion, ratings and anything confidential belong in Teams.

## Team distribution in Microsoft 365 (standard connectors, no premium)
- **Weekly card in Teams:** Power Automate → *Automated cloud flow*.
  - Trigger: **RSS: When a feed item is published**, URL = `<site>/digest.xml`
  - Action: **Teams: Post message in a chat or channel** → your team channel
  - Message: title, link and summary
- **Site as a Teams tab:** in the channel, **+ → Website** → the site URL.
- **Must-read tracker:** a Microsoft List in the team's SharePoint with columns Title, Link, Lens, Owner, Takeaway, Rating.

## Maintenance
- **One config file:** `config/queries.yaml` holds the queries, lenses, device terms, feeds and weights.
- **Events:** `config/events.yaml`, reviewed quarterly by a rotating owner. Entries marked `verify: true` have unconfirmed dates.
- **Failures:** GitHub emails the repo owner when a run fails. If one source fails, it's logged and skipped, and the rest of the run continues.
- **Removed feeds:** Fierce Biotech blocks automated readers (HTTP 403), so it isn't included.

## Roadmap
- **Phase 2:** a weekly audio episode (Kokoro TTS) published as `docs/podcast.xml`.
- **Phase 3:** a weekly quiz, key-numbers flashcards and a monthly "state of the field" summary.
