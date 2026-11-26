"""Mercado Livre pela API oficial (precisa de ML_CLIENT_ID e ML_CLIENT_SECRET nas variáveis de ambiente).

Só entram lojas oficiais (`official_store_id` preenchido) e itens novos. O preço é o `price` do resultado.
Sem as credenciais, `configurado()` devolve False e o coletor pula o Mercado Livre sem falhar.
"""
import os
import time

import requests

API = "https://api.mercadolibre.com"
HEADERS = {"User-Agent": "MuquiranaTech/1.0", "Accept": "application/json"}
_token = {"v": None, "ate": 0}


class Blocked(Exception):
    """A API recusou o acesso (credenciais erradas ou limite): parar a loja nesta rodada."""


def configurado():
    return bool(os.environ.get("ML_CLIENT_ID") and os.environ.get("ML_CLIENT_SECRET"))


def token():
    if _token["v"] and time.time() < _token["ate"]:
        return _token["v"]
    r = requests.post(f"{API}/oauth/token", headers=HEADERS, timeout=30, data={
        "grant_type": "client_credentials",
        "client_id": os.environ["ML_CLIENT_ID"],
        "client_secret": os.environ["ML_CLIENT_SECRET"]})
    if r.status_code in (400, 401, 403):
        raise Blocked(f"token recusado ({r.status_code})")
    r.raise_for_status()
    j = r.json()
    _token.update(v=j["access_token"], ate=time.time() + j.get("expires_in", 3600) - 60)
    return _token["v"]


def _item(o):
    price = o.get("price")
    if not o.get("official_store_id") or o.get("condition") != "new" or not price or price <= 0:
        return None
    thumb = o.get("thumbnail") or ""
    return {
        "code": str(o["id"]),
        "name": o["title"],
        "price": round(float(price), 2),
        "list_price": round(max(float(o.get("original_price") or 0), float(price)), 2),
        "seller": "Loja oficial",
        "img": thumb.replace("http://", "https://").replace("-I.jpg", "-O.jpg") or None,
        "url": o.get("permalink"),
        "available": (o.get("available_quantity") or 0) > 0,
        "offer_ends": None,
    }


def parse(data):
    out = []
    for o in (data or {}).get("results", []):
        it = _item(o)
        if it:
            out.append(it)
    return out


def search(term):
    r = requests.get(f"{API}/sites/MLB/search", headers={**HEADERS, "Authorization": f"Bearer {token()}"},
                     params={"q": term.replace("-", " "), "official_store": "all", "condition": "new", "limit": 30},
                     timeout=30)
    if r.status_code in (401, 403, 429):
        raise Blocked(f"busca recusada ({r.status_code})")
    r.raise_for_status()
    return parse(r.json())
