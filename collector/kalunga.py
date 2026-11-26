"""Leitura da Kalunga (loja própria, sem marketplace): lista de busca em HTML.

Cada produto da busca é um bloco `blocoproduto` com título, link `/prod/<nome>/<código>`, preço atual
(`blocoproduto__price`, "à vista" quando há desconto) e, às vezes, o preço "De:" riscado.
`search(termo)` devolve os itens no mesmo formato do kabum.py. `preco_pagina(url)` lê o preço direto da
página do produto (usado para conferir).
"""
import html as _html
import re

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
BASE = "https://www.kalunga.com.br"
PRECO = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})")


class Blocked(Exception):
    pass


def _num(txt):
    m = PRECO.search(txt or "")
    return float(m.group(1).replace(".", "").replace(",", ".")) if m else None


def parse(page):
    out, vistos = [], set()
    page = re.sub(r"data:image[^\"']*", "", page or "")
    for bloco in re.split(r'(?=<div class="blocoproduto\s)', page)[1:]:
        link = re.search(r'href="(/prod/[^"]+/(\d+))"', bloco)
        titulo = re.search(r'<h2 class="blocoproduto__title[^"]*">(.*?)</h2>', bloco, re.S)
        preco = re.search(r'class="[^"]*blocoproduto__price[^"]*">(.*?)</span>(?:</span>)?', bloco, re.S)
        if not (link and titulo and preco):
            continue
        code = link.group(2)
        price = _num(re.sub(r"<[^>]+>", " ", preco.group(1)))
        if code in vistos or not price:
            continue
        vistos.add(code)
        velho = re.search(r'blocoproduto__oldprice[^>]*>(.*?)</del>', bloco, re.S)
        list_price = max(_num(velho.group(1)) or 0, price) if velho else price
        img = re.search(r'data-src="(https://img\.kalunga\.com\.br/[^"]+\.(?:jpg|png))"', bloco)
        out.append({
            "code": code,
            "name": _html.unescape(re.sub(r"<[^>]+>", "", titulo.group(1))).strip(),
            "price": price,
            "list_price": list_price,
            "seller": "Kalunga",
            "img": img.group(1) if img else None,
            "url": BASE + link.group(1),
            "available": True,  # a busca só mostra itens com botão "Comprar"
            "offer_ends": None,
        })
    return out


def search(term):
    r = requests.get(f"{BASE}/busca/{term.replace(' ', '-')}", headers=HEADERS, timeout=30)
    if r.status_code in (403, 429, 503):
        raise Blocked(f"HTTP {r.status_code}")
    r.raise_for_status()
    return parse(r.text)


def preco_ficha(t):
    """Preço que a ficha do produto mostra: o "à vista" (campo txtPrecoVista) quando existe; senão o preço
    único da loja (último "price" do dataLayer)."""
    m = re.search(r'id="hfprecovista">(R\$\s*[\d.]+,\d{2})', t) or re.search(r'id="hfprecovenda">(R\$\s*[\d.]+,\d{2})', t)
    if m:  # o preço do cabeçalho fixo da ficha: é o que o cliente vê
        return _num(m.group(1))
    m = re.search(r'id="txtPrecoVista"[^>]*value="(R\$\s*[\d.]+,\d{2})"', t)
    if m:
        return _num(m.group(1))
    todos = re.findall(r'"price"\s*:\s*(\d+(?:\.\d+)?)', t)
    return float(todos[-1]) if todos else None


def preco_pagina(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return preco_ficha(r.text)


def refinar(item):
    """A lista da busca nem sempre traz o mesmo preço da ficha (desconto à vista): confirma na ficha."""
    preco = preco_pagina(item["url"])
    if not preco:
        return None
    return {**item, "price": preco, "list_price": max(item["list_price"], preco)}
