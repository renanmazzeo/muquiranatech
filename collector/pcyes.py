"""Loja oficial da PCYes (www.pcyes.com.br), parceira da Lomadee.

O site é Next.js sobre Magento: cada página de categoria já traz os produtos (12 por página) no `__NEXT_DATA__`,
com `price_range.minimum_price.final_price` (o preço que a ficha mostra, igual no Pix e em até 10x sem juros,
conferido em 27/11/2026) e `regular_price` (o "de"). `/graphql` e `/search` são proibidos no robots.txt, e as
outras páginas da categoria só carregam pelo `/graphql`: por isso o catálogo lê a 1ª página de cada uma das
categorias do sitemap (`/sitemap/categories.xml`), o que cobre os produtos principais com ~55 acessos.
"""
import json
import re
import time

import requests

BASE = "https://www.pcyes.com.br"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
FORA = ("drivers-e-manuais", "camisetas", "monte-seu-pc")  # páginas sem produto de tecnologia


class Blocked(Exception):
    pass


def _num(v):
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return 0.0


def _item(p):
    if p.get("stock_status") != "IN_STOCK" or not p.get("url_key") or not p.get("sku"):
        return None
    mp = (p.get("price_range") or {}).get("minimum_price") or {}
    price = _num((mp.get("final_price") or {}).get("value"))
    if price <= 0:
        return None
    try:
        imgs = json.loads(p.get("cdn_images") or "[]")
    except ValueError:
        imgs = []
    return {
        "code": str(p["sku"]),
        "name": " ".join(str(p.get("name") or "").split()),
        "price": price,
        "list_price": max(_num((mp.get("regular_price") or {}).get("value")), price),
        "seller": "PCYes",
        "img": imgs[0] if imgs else None,
        "url": f"{BASE}/{p['url_key']}",
        "available": True,
        "offer_ends": None,
    }


def parse(page_html):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page_html or "", re.S)
    if not m:
        return []
    itens = (((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("products") or {}).get("items") or []
    return [x for x in (_item(p) for p in itens) if x]


def _get(url):
    r = requests.get(url, headers=HEADERS, timeout=40)
    if r.status_code in (403, 429):
        raise Blocked(f"HTTP {r.status_code}")
    r.raise_for_status()
    return r.text


def categorias():
    return [u for u in re.findall(r"<loc>([^<]+)</loc>", _get(BASE + "/sitemap/categories.xml"))
            if not any(f in u for f in FORA)]


def catalogo(path="sitemap", pausa=3.0):
    """Produtos em estoque da 1ª página de cada categoria do sitemap (sem repetir)."""
    out = {}
    for i, url in enumerate(categorias()):
        time.sleep(pausa)
        try:
            for it in parse(_get(url)):
                out.setdefault(it["code"], it)
        except Blocked:
            raise
        except Exception as e:  # noqa: BLE001 — uma categoria com erro não derruba as outras
            print(f"  ! PCYes {url}: {e}")
    return list(out.values())
