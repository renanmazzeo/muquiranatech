"""Leitura de jogos da Steam (API pública da loja, em reais).

`search(termo)` usa `api/storesearch` (já traz o preço final em centavos) e devolve os itens no mesmo
formato do kabum.py. `detalhes(appid)` consulta `api/appdetails` (usado para conferir preços).
`catalogo("topsellers")` lê a lista de jogos mais vendidos no Brasil (`search/results`, só jogos: category1=998)
e pega o preço de cada um em lote pelo `api/appdetails` (o preço do jogo base, o mesmo da página do jogo;
a lista da busca às vezes mostra o preço de uma edição ou pacote). Jogo grátis fica de fora.
Preço da Steam = preço final de hoje, sem desconto extra no Pix.
"""
import html
import re
import time

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


LINHA = re.compile(r'<a href="https://store\.steampowered\.com/app/(\d+)/[^"]*"[^>]*data-ds-itemkey="App_\d+"[^>]*>(.*?)</a>', re.S)
TITULO = re.compile(r'<span class="title">(.*?)</span>', re.S)


def lista(results_html):
    """[(appid, nome)] de uma página de resultados da busca da loja."""
    out = []
    for appid, corpo in LINHA.findall(results_html or ""):
        t = TITULO.search(corpo)
        if t:
            out.append((appid, html.unescape(t.group(1)).strip()))
    return out


def precos(appids, pausa=1.5):
    """{appid: (final, inicial)} em reais, pelo appdetails em lotes (só jogos pagos com preço em BRL)."""
    out = {}
    for i in range(0, len(appids), 100):
        if i:
            time.sleep(pausa)
        r = requests.get(f"{API}/appdetails", headers=HEADERS, timeout=40,
                         params={"appids": ",".join(appids[i:i + 100]), "cc": "br", "filters": "price_overview"})
        r.raise_for_status()
        for appid, d in r.json().items():
            po = (d.get("data") or {}).get("price_overview") if d.get("success") and isinstance(d.get("data"), dict) else None
            if po and po.get("currency") == "BRL" and po.get("final", 0) > 0:
                out[appid] = (round(po["final"] / 100, 2), round(max(po.get("initial") or 0, po["final"]) / 100, 2))
    return out


def catalogo(filtro="topsellers", max_paginas=5, pausa=3.0):
    """Os jogos de uma lista da loja (ex.: "topsellers"), 100 por página, com o preço da página do jogo."""
    nomes = {}
    for pagina in range(max_paginas):
        if pagina:
            time.sleep(pausa)
        r = requests.get("https://store.steampowered.com/search/results/", headers=HEADERS, timeout=40,
                         params={"filter": filtro, "category1": 998, "cc": "br", "l": "portuguese",
                                 "start": pagina * 100, "count": 100, "infinite": 1})
        r.raise_for_status()
        achados = lista(r.json().get("results_html"))
        for appid, nome in achados:
            nomes.setdefault(appid, nome)
        if len(achados) < 50:
            break
    out = []
    for appid, (final, inicial) in precos(list(nomes), pausa=pausa).items():
        it = _item({"id": appid, "name": nomes[appid], "price": {"final": round(final * 100), "initial": round(inicial * 100)}})
        if it:
            out.append(it)
    return out
