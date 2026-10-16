"""Shared HTTP session with retries and a polite User-Agent."""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

UA = "PancreasRadar/0.1 (academic literature monitor)"


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=("GET", "POST"))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s
