"""Leitura de jogos da Steam (API pública da loja, em reais).

`search(termo)` usa `api/storesearch` (já traz o preço final em centavos) e devolve os itens no mesmo
formato do kabum.py. `detalhes(appid)` consulta `api/appdetails` (usado para conferir preços).
Preço da Steam = preço final de hoje, sem desconto extra no Pix.
"""
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MuquiranaTech/1.0)", "Accept-Language": "pt-BR,pt;q=0.9"}
API = "https://store.steampowered.com/api"


def _item(o):
    pr = o.get("price") or {}
    final, initial = pr.get("final"), pr.get("initial")
    if not o.get("id") or not final or final <= 0 or pr.get("currency", "BRL") != "BRL":
        return None  # sem preço (grátis, não lançado) ou em outra moeda
    code = str(o["id"])
    return {
        "code": code,
        "name": o["name"],
        "price": round(final / 100, 2),
        "list_price": round(max(initial or 0, final) / 100, 2),
        "seller": "Steam",
        "img": f"https://cdn.akamai.steamstatic.com/steam/apps/{code}/header.jpg",
        "url": f"https://store.steampowered.com/app/{code}/",
        "available": True,
        "offer_ends": None,
    }


def parse(data):
    out = []
    for o in (data or {}).get("items", []):
        if o.get("type", "app") != "app":
            continue
        it = _item(o)
        if it:
            out.append(it)
    return out


def search(term):
    r = requests.get(f"{API}/storesearch/", params={"term": term, "cc": "br", "l": "portuguese"},
                     headers=HEADERS, timeout=30)
    r.raise_for_status()
    return parse(r.json())


def detalhes(appid):
    """Preço final e inicial (em reais) de um jogo, direto da API de detalhes."""
    r = requests.get(f"{API}/appdetails", params={"appids": appid, "cc": "br", "filters": "price_overview"},
                     headers=HEADERS, timeout=30)
    r.raise_for_status()
    d = r.json().get(str(appid)) or {}
    po = (d.get("data") or {}) if d.get("success") else {}
    po = po.get("price_overview") if isinstance(po, dict) else None
    if not po:
        return None
    return {"final": po["final"] / 100, "initial": po["initial"] / 100, "desconto": po.get("discount_percent", 0)}
