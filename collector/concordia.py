"""Concórdia Informática (www.concordia.inf.br), loja da plataforma Tray, parceira da Lomadee.

As páginas de categoria (`/<categoria>?pg=N`, permitidas no robots.txt) trazem cada produto num bloco
`data-product-container-id` com nome, link, foto, preço "De", preço "Por" e o preço "à vista com desconto",
que é o que a ficha do produto também mostra (conferido em 27/11/2026) e é o preço que o site usa.
Produto "Esgotado!" fica de fora. A seção "Outlet" (mostruário) não é lida.
"""
import html
import re
import time

import requests

BASE = "https://www.concordia.inf.br"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


class Blocked(Exception):
    pass


def _reais(txt):
    m = re.search(r"([\d.]+)\s*,\s*(\d{2})", txt or "")
    return round(float(m.group(1).replace(".", "") + "." + m.group(2)), 2) if m else 0.0


def _texto(h):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def _bloco(pid, b):
    nome = re.search(r'data-ga4-name="([^"]+)"', b)
    link = re.search(r'class="product__link"\s+href="([^"]+)"', b)
    if not (nome and link):
        return None
    t = _texto(b[:b.find("product__offer") + 4000] if "product__offer" in b else b[:6000])
    if "Esgotado" in t or "Indisponível" in t:
        return None
    vista = re.search(r"R\$\s*([\d.]+\s*,\s*\d{2})\s*à vista", t)
    por = re.search(r"Por:\s*R\$\s*([\d.]+,\d{2})", t)
    de = re.search(r"De:?\s*R\$\s*([\d.]+,\d{2})", t)
    price = _reais(vista.group(1)) if vista else (_reais(por.group(1)) if por else 0.0)
    if price <= 0:
        return None
    img = re.search(r'data-original="(https://images\.tcdn\.com\.br/[^"]+)"', b)
    lista = max(_reais(de.group(1)) if de else 0.0, _reais(por.group(1)) if por else 0.0, price)
    return {
        "code": pid,
        "name": " ".join(html.unescape(nome.group(1)).split()),
        "price": price,
        "list_price": lista,
        "seller": "Concórdia Informática",
        "img": img.group(1) if img else None,
        "url": link.group(1),
        "available": True,
        "offer_ends": None,
    }


def parse(page_html):
    out, vistos = [], set()
    # os blocos do menu (vitrine "compacta" no topo) repetem produtos: o código evita duplicar
    for parte in (page_html or "").split('data-product-container-id="')[1:]:
        pid = parte.split('"', 1)[0]
        if pid in vistos:
            continue
        it = _bloco(pid, parte)
        if it:
            vistos.add(pid)
            out.append(it)
    return out


def _get(url):
    r = requests.get(url, headers=HEADERS, timeout=40)
    if r.status_code in (403, 429):
        raise Blocked(f"HTTP {r.status_code}")
    r.raise_for_status()
    r.encoding = r.encoding or "iso-8859-1"
    return r.text


def catalogo(path, max_paginas=30, pausa=3.0):
    """Produtos disponíveis de uma categoria (ex.: "notebooks"), página por página (?pg=N)."""
    out, pagina = {}, 1
    while pagina <= max_paginas:
        h = _get(f"{BASE}/{path.strip('/')}" + (f"?pg={pagina}" if pagina > 1 else ""))
        antes = len(out)
        for it in parse(h):
            out.setdefault(it["code"], it)
        if len(out) == antes or f"pg={pagina + 1}" not in h:
            break
        pagina += 1
        time.sleep(pausa)
    return list(out.values())
