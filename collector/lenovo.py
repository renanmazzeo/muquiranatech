"""Loja oficial da Lenovo (www.lenovo.com/br/pt), pela mesma API que as páginas de categoria usam.

`catalogo(filtro)` lê uma categoria inteira. `filtro` é o "pageFilterId" da página da categoria
(laptops, desktops, monitores; ver watchlist). A lista da categoria às vezes atrasa R$ 1 em relação à ficha,
então o preço final vem da mesma API que a ficha do produto usa (`/detail/price/batch/get`, 20 códigos por
pedido): é o "À vista no PIX" (conferido em 26/11/2026). Produto sem preço na ficha fica de fora.
Só entra o que está disponível para compra. A Lenovo vende tudo direto, então o vendedor é sempre a Lenovo.
As páginas de busca (/search) são proibidas no robots.txt: por isso não existe `search()`.
"""
import json
import time
from urllib.parse import quote

import requests

BASE = "https://www.lenovo.com/br/pt"
API = "https://openapi.lenovo.com/br/pt/ofp/search/dlp/product/query/get/_tsc"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Referer": BASE + "/laptops/",
}
POR_PAGINA = 20


class Blocked(Exception):
    pass


def _num(v):
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return 0.0


def _item(p):
    if p.get("marketingStatus") != "Available" or p.get("inventoryStatus") != 1 or not p.get("purchaseFlag"):
        return None
    price = _num(p.get("finalPrice"))
    if price <= 0 or not p.get("url"):
        return None
    nome = (p.get("summary") or p.get("productName") or "").strip()
    if "lenovo" not in nome.lower():
        nome = "Lenovo " + nome
    thumb = ((p.get("media") or {}).get("thumbnail") or {}).get("imageAddress")
    return {
        "code": str(p.get("productCode") or p["id"]),
        "name": nome,
        "price": price,
        "list_price": max(_num(p.get("webPrice")), price),
        "seller": "Lenovo",
        "img": ("https:" + thumb if thumb and thumb.startswith("//") else thumb),
        "url": BASE + p["url"],
        "available": True,
        "offer_ends": None,
    }


def parse(resp):
    grupos = ((resp or {}).get("data") or {}).get("data") or []
    return [x for g in grupos for x in (_item(p) for p in g.get("products") or []) if x]


def _get(filtro, pagina):
    params = {"classificationGroupIds": "400001", "pageFilterId": filtro, "facets": [], "page": str(pagina),
              "pageSize": POR_PAGINA, "groupCode": "", "init": pagina == 1, "sorts": ["priceUp"], "version": "v2",
              "enablePreselect": True, "badgeSort": False, "clickedSort": True, "subseriesCode": ""}
    q = {"pageFilterId": filtro, "subSeriesCode": "", "loyalty": "false",
         "params": quote(json.dumps(params, separators=(",", ":")))}
    r = requests.get(API, headers=HEADERS, params=q, timeout=40)
    if r.status_code in (403, 429):
        raise Blocked(f"HTTP {r.status_code}")
    r.raise_for_status()
    if "json" not in (r.headers.get("content-type") or ""):
        raise Blocked("resposta sem JSON")
    return r.json()


PRECO = "https://openapi.lenovo.com/br/pt/detail/price/batch/get"


def precos(codigos, pausa=2.0):
    """{código: (preço Pix, preço "de")} pela API da ficha do produto."""
    out = {}
    for i in range(0, len(codigos), 20):
        if i:
            time.sleep(pausa)
        r = requests.get(PRECO, headers=HEADERS, timeout=40,
                         params={"preSelect": "1", "mcode": ",".join(codigos[i:i + 20]), "configId": "", "enteredCode": ""})
        if r.status_code in (403, 429):
            raise Blocked(f"HTTP {r.status_code}")
        r.raise_for_status()
        out.update(ler_precos(r.json()))
    return out


def ler_precos(j):
    out = {}
    for code, e in ((j or {}).get("data") or {}).items():
        if not isinstance(e, list) or len(e) < 5 or e[1] != "ok":
            continue
        preco = _num(e[4])
        de = _num(e[13][3]) if len(e) > 13 and isinstance(e[13], list) and len(e[13]) > 3 else 0
        if preco > 0:
            out[code] = (preco, max(de, preco))
    return out


def catalogo(filtro, max_paginas=20, pausa=2.0):
    """Todos os produtos disponíveis de uma categoria (filtro = pageFilterId da página)."""
    out, pagina, total = {}, 1, 1
    while pagina <= min(total, max_paginas):
        j = _get(filtro, pagina)
        total = ((j.get("data") or {}).get("pageCount")) or 1
        for it in parse(j):
            out.setdefault(it["code"], it)
        pagina += 1
        if pagina <= total:
            time.sleep(pausa)
    pr = precos(list(out), pausa=pausa)
    final = []
    for code, it in out.items():
        if code in pr:
            it["price"], it["list_price"] = pr[code]
            final.append(it)
    return final
