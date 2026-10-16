"""Each source module exposes fetch(cfg, since: date, until: date) -> list[dict].

Item schema (all sources):
  id, source, type, title, url, date (YYYY-MM-DD), abstract, venue, tags (list[str]), extra (dict)
"""
