"""Leitura de produtos da KaBuM! (páginas de busca/categoria, ao vivo ou arquivadas na Wayback).

A KaBuM! usa Next.js: cada página traz um <script id="__NEXT_DATA__"> com a lista de
produtos (código, nome, foto, preço à vista, preço cheio, vendedor). O parser procura
essa lista em qualquer lugar do JSON, para continuar funcionando em páginas antigas.
"""
import json
import re
import time
import unicodedata

import requests

BASE = "https://www.kabum.com.br"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def norm(s):
    """minúsculas, sem acento, hífen vira espaço — para comparar nomes."""
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.lower().replace("-", " "))


def _num(x):
    try:
        v = float(x)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def _offer(o, at):
    """Oferta relâmpago/Black Friday ("OFERTAS KABUM") válida no instante `at`, aberta a todos e com estoque."""
    of = o.get("offer")
    if not isinstance(of, dict) or of.get("isPrimeExclusive") or of.get("isLoggedUserExclusive"):
        return None
    try:
        if not of["startsAt"] <= at <= of["endsAt"]:
            return None
    except (KeyError, TypeError):
        return None
    if "quantityAvailable" in of and not of["quantityAvailable"]:
        return None
    return of


def _item(o, at=None):
    """`at` = instante (epoch) em que a página foi vista: agora, ou a data da cópia na Wayback."""
    of = _offer(o, time.time() if at is None else at)
    src = of or o  # durante uma oferta, o preço que vale é o dela
    price = _num(src.get("priceWithDiscount")) or _num(src.get("price"))
    if not price:
        return None
    code = str(o["code"])
    friendly = o.get("friendlyName") or ""
    img = o.get("image")
    if not isinstance(img, str):
        imgs = o.get("images") or []
        img = imgs[0] if imgs and isinstance(imgs[0], str) else None
    list_price = max(v for v in (_num(o.get("oldPrice")), _num(o.get("price")), _num(src.get("price")), price) if v)
    flags = o.get("flags") or {}
    if flags.get("isOpenbox"):  # produto de mostruário / caixa aberta: fora
        return None
    available = o["available"] if "available" in o else (o.get("quantity") or 0) > 0
    return {
        "code": code,
        "name": o["name"],
        "price": round(price, 2),  # preço à vista (PIX)
        "list_price": round(list_price, 2),  # preço "de" / parcelado
        "seller": o.get("sellerName") or "KaBuM!",
        "img": img,
        "url": f"{BASE}/produto/{code}/{friendly}" if friendly else f"{BASE}/produto/{code}",
        "available": bool(available),
        "offer_ends": of["endsAt"] if of else None,
    }


def parse(html, at=None):
    """Extrai todos os produtos de uma página da KaBuM! (na ordem em que aparecem).
    `at` (epoch): quando a página foi vista, para saber quais ofertas valiam. Padrão: agora."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    found = {}

    def walk(o, depth=0):
        if depth > 14:
            return
        if isinstance(o, str):
            # às vezes a KaBuM! guarda o catálogo como JSON dentro de uma string
            if len(o) > 200 and o[:1] in "{[":
                try:
                    walk(json.loads(o), depth + 1)
                except ValueError:
                    pass
        elif isinstance(o, dict):
            if "code" in o and "name" in o and ("priceWithDiscount" in o or "price" in o):
                it = _item(o, at)
                if it and it["code"] not in found:
                    found[it["code"]] = it
            for v in o.values():
                walk(v, depth + 1)
        elif isinstance(o, list):
            for v in o:
                walk(v, depth + 1)

    walk(json.loads(m.group(1)))
    return list(found.values())


def search(term):
    r = requests.get(f"{BASE}/busca/{term}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return parse(r.text)


# filtro "Vendido pela KaBuM!" da própria loja (facet_filters = JSON em base64)
SO_KABUM = "eyJrYWJ1bV9wcm9kdWN0IjpbInRydWUiXX0="  # {"kabum_product":["true"]}


def catalogo(path, max_paginas=40, pausa=3.0):
    """Todos os produtos VENDIDOS PELA PRÓPRIA KaBuM! numa categoria (ex.: "/hardware/placa-de-video-vga"),
    100 por página. Sem parâmetro de ordenação: o robots.txt da KaBuM! pede que robôs não usem "sort"."""
    itens, pagina, total = {}, 1, 1
    while pagina <= min(total, max_paginas):
        r = requests.get(f"{BASE}{path}?page_number={pagina}&page_size=100&facet_filters={SO_KABUM}",
                         headers=HEADERS, timeout=40)
        r.raise_for_status()
        m = re.search(r'totalPagesCount\\?":(\d+)', r.text)
        total = int(m.group(1)) if m else 1
        for it in parse(r.text):
            itens.setdefault(it["code"], it)
        pagina += 1
        if pagina <= min(total, max_paginas):
            time.sleep(pausa)
    return list(itens.values())


def pick(items, must=(), limit=4, sellers=("KaBuM!",), exclude=()):
    """Só vendedores confiáveis (KaBuM! e parceiros grandes), disponíveis, com as palavras exigidas
    e sem as palavras proibidas (ex.: busca "ssd 2tb" não pode trazer um PS5 "com SSD de 2TB")."""
    must = [norm(w) for w in must]
    exclude = [norm(w) for w in exclude]
    ok = {norm(s) for s in sellers}
    out = []
    for it in items:
        if norm(it["seller"]) not in ok or not it["available"]:
            continue
        name = norm(it["name"])
        if all(w in name for w in must) and not any(w in name for w in exclude):
            out.append(it)
        if len(out) >= limit:
            break
    return out
