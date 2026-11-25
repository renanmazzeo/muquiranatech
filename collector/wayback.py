"""Cópias antigas de páginas via Wayback Machine (Internet Archive) — gratuito."""
import time

import requests

CDX = "https://web.archive.org/cdx/search/cdx"
HEADERS = {"User-Agent": "MuquiranaTech-price-history/0.1 (historico de precos)"}


def _get(url, params=None, tries=4):
    for n in range(tries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=90)
            if r.status_code in (429, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r
        except requests.RequestException:
            if n == tries - 1:
                raise
            time.sleep(10 * (n + 1))


def snapshots(url, since="2023", per_month=2):
    """Lista (timestamp, url_original) das cópias com status 200, no máx. `per_month` por mês."""
    r = _get(CDX, {
        "url": url, "output": "json", "fl": "timestamp,original",
        "filter": "statuscode:200", "from": since, "collapse": "timestamp:8",
    })
    rows = r.json()[1:] if r.text.strip() else []
    count, out = {}, []
    for ts, original in rows:
        month = ts[:6]
        if count.get(month, 0) < per_month:
            count[month] = count.get(month, 0) + 1
            out.append((ts, original))
    return out


def fetch(ts, original):
    """HTML original da cópia (o sufixo id_ evita a barra/reescrita da Wayback)."""
    return _get(f"https://web.archive.org/web/{ts}id_/{original}").text
