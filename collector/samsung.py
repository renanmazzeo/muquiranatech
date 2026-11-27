"""Loja oficial da Samsung (shop.samsung.com/br), pela API pública de catálogo da plataforma VTEX.

`catalogo(cat)` lê uma categoria inteira (ex.: "4/8" = Mobile > Smartphone), 50 produtos por pedido.
O preço que vale é o do **Pix à vista** (o mesmo que a loja mostra e que a simulação do carrinho confirma);
sem Pix, o preço normal. Só entra o que a própria Samsung vende (seller "1") e está disponível.
"""
import time

import requests

import parcelas

BASE = "https://shop.samsung.com/br"
API = BASE + "/api/catalog_system/pub/products/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


class Blocked(Exception):
    pass


def _oferta(item):
    """(preço Pix ou à vista, preço "de", disponível) da Samsung para um SKU; None se não for vendido por ela."""
    for s in item.get("sellers") or []:
        if str(s.get("sellerId")) != "1":
            continue
        o = s.get("commertialOffer") or {}
        price = o.get("Price") or 0
        if price <= 0:
            return None
        pix = [i["Value"] for i in o.get("Installments") or []
               if i.get("PaymentSystemName", "").lower() == "pix" and i.get("NumberOfInstallments") == 1]
        avista = min(pix) if pix else price
        return round(avista, 2), round(max(o.get("ListPrice") or 0, price), 2), (o.get("AvailableQuantity") or 0) > 0
    return None


def _item(p):
    """Um produto = o SKU disponível mais barato (cores do mesmo modelo têm o mesmo preço)."""
    melhor = None
    for it in p.get("items") or []:
        of = _oferta(it)
        if of and of[2] and (melhor is None or of[0] < melhor[1][0]):
            melhor = (it, of)
    if not melhor:
        return None
    it, (price, list_price, _) = melhor
    imgs = it.get("images") or []
    return {
        "code": str(p["productId"]),
        "name": p["productName"].strip(),
        "price": price,
        "list_price": max(list_price, price),
        "seller": "Samsung",
        "img": imgs[0]["imageUrl"] if imgs else None,
        "url": p.get("link") or f"{BASE}/{p.get('linkText')}/p",
        "available": True,
        "offer_ends": None,
        "parc": parcelas.vtex(next((s.get("commertialOffer", {}).get("Installments") for s in it.get("sellers") or []
                                    if str(s.get("sellerId")) == "1"), None)),
    }


def parse(produtos):
    return [x for x in (_item(p) for p in produtos or []) if x]


def _get(params):
    r = requests.get(API, headers=HEADERS, params=params, timeout=40)
    if r.status_code in (403, 429):
        raise Blocked(f"HTTP {r.status_code}")
    if r.status_code not in (200, 206):
        r.raise_for_status()
    if "json" not in (r.headers.get("content-type") or ""):
        raise Blocked("resposta sem JSON")
    return r.json()


def catalogo(path, max_paginas=20, pausa=2.0):
    """Todos os produtos de uma categoria (path = ids da árvore, ex.: "4/8")."""
    out, pagina = {}, 0
    while pagina < max_paginas:
        lote = _get({"fq": f"C:/{path.strip('/')}/", "_from": pagina * 50, "_to": pagina * 50 + 49})
        for it in parse(lote):
            out.setdefault(it["code"], it)
        if len(lote) < 50:
            break
        pagina += 1
        time.sleep(pausa)
    return list(out.values())


def search(term):
    return parse(_get({"ft": term, "_from": 0, "_to": 49}))
