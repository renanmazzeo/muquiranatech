"""Loja oficial da Xiaomi no Brasil (www.mibrasil.com.br), parceira da Lomadee.

A loja é Linx Commerce: `/products.json?pg=N` (permitido no robots.txt; só `/produtos` e `/pesquisa` são proibidos)
devolve o catálogo inteiro, 15 produtos por página, com o mesmo JSON de preço que a ficha usa. A ficha mostra
"De R$ X, Por R$ Y com 8% de desconto à vista, ou R$ Z em 12x sem juros" (conferido em 27/11/2026):
- preço do site = `BestInstallment.InstallmentPrice` quando é pagamento em 1x com desconto (o "Por ... à vista");
  sem desconto à vista, `SalesPrice`;
- "de" = `ListPrice`; parcelamento = `MaxInstallmentsNoInterest` (sempre sem juros).
Só produto com `Availability` "I" (em estoque). Vendedor é sempre a própria loja oficial.
"""
import time

import requests

import categorias
import parcelas
from kabum import norm

BASE = "https://www.mibrasil.com.br"
CDN = "https://d1r6yjixh9u0er.cloudfront.net"  # onde a própria loja serve as fotos
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "application/json",
}
# categoria final da loja (LeafCategoryName, sem acento e minúscula) -> categoria do site. O que não está aqui
# (capas, películas, pulseiras de reposição, beleza, pet, mochilas, utensílios...) fica de fora.
CATS = {
    "smartphones": "celular", "celulares": "celular", "carregadores e power banks": "celular", "cabos": "celular",
    "tablets": "tablet",
    "pulseiras inteligentes": "wear", "relogios inteligentes": "wear", "smartwatch": "wear",
    "fone de ouvido sem fio": "audio", "fone de ouvido com fio": "audio", "caixa de som": "audio", "audio": "audio",
    "assistente virtual": "audio",
    "seguranca": "casa", "iluminacao": "casa", "casa inteligente": "casa",
    "roteadores e perifericos": "?rede",  # roteador -> rede, mouse -> perif (pelo nome)
    "tv inteligente": "tv",
    "utilidades domesticas": "?robo",  # só os robôs aspiradores (o resto é peça de reposição e cozinha)
}


class Blocked(Exception):
    pass


def _num(v):
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return 0.0


def categoria(p):
    """Categoria do site, ou None quando o produto não é de tecnologia."""
    cat = CATS.get(norm(p.get("LeafCategoryName") or "").strip())
    nome = norm(p.get("Name") or "").strip()
    if cat == "?robo":
        return "casa" if nome.startswith("robo aspirador") else None
    if cat == "?rede":
        return categorias.classificar(p.get("Name") or "", "rede")
    return cat


def _item(p):
    if p.get("Availability") != "I" or not p.get("Url") or not p.get("ProductID"):
        return None
    cat = categoria(p)
    if not cat:
        return None
    pr = p.get("Price") or {}
    cheio = _num(pr.get("SalesPrice"))
    bi = pr.get("BestInstallment") or {}
    price = cheio
    if bi.get("Installments") == 1 and _num(bi.get("Discount")) > 0 and 0 < _num(bi.get("InstallmentPrice")) < cheio:
        price = _num(bi.get("InstallmentPrice"))  # "Por R$ ... à vista"
    if price <= 0:
        return None
    mx = pr.get("MaxInstallmentsNoInterest") or {}
    parc = None
    if (mx.get("Installments") or 0) > 1:
        parc = parcelas.montar(mx["Installments"], _num(mx.get("InstallmentPrice")), _num(mx.get("RetailPrice")) or None,
                               juros=False)
    # a foto fica na CDN da loja (o mesmo caminho em www.mibrasil.com.br dá 404); tamanho médio, 500 px
    grupo = (p.get("MediaGroups") or [{}])[0] or {}
    img = (grupo.get("Medium") or {}).get("MediaPath") or p.get("MediaSmall")
    return {
        "code": str(p["ProductID"]),
        "name": " ".join(str(p.get("Name") or "").split()),
        "price": price,
        "list_price": max(_num(pr.get("ListPrice")), cheio, price),
        "seller": "Xiaomi",
        "img": (CDN + img if img.startswith("/") else img) if img else None,
        "url": BASE + p["Url"] if p["Url"].startswith("/") else p["Url"],
        "available": True,
        "offer_ends": None,
        "parc": parc,
        "cat": cat,
    }


def parse(dados):
    grid = ((dados or {}).get("Model") or {}).get("Grid") or {}
    return [x for x in (_item(p) for p in grid.get("Products") or []) if x], grid.get("PageCount") or 1


def _get(pagina):
    r = requests.get(f"{BASE}/products.json" + (f"?pg={pagina}" if pagina > 1 else ""), headers=HEADERS, timeout=40)
    if r.status_code in (403, 429):
        raise Blocked(f"HTTP {r.status_code}")
    r.raise_for_status()
    return r.json()


def catalogo(path="tudo", pausa=3.0, max_paginas=60):
    """O catálogo inteiro da loja, página por página (sem repetir)."""
    out, pagina, total = {}, 1, 1
    while pagina <= min(total, max_paginas):
        itens, total = parse(_get(pagina))
        for it in itens:
            out.setdefault(it["code"], it)
        pagina += 1
        time.sleep(pausa)
    return list(out.values())
