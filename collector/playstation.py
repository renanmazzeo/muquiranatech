"""Leitura de jogos da PlayStation Store (loja oficial da Sony, em reais).

A página de busca só mostra os preços depois que o JavaScript roda, por isso a busca usa o navegador
(Playwright). Cada cartão de jogo traz nome, id e preço em `data-telemetry-meta`. Preço de hoje = o do
cartão ("discount" é o preço com desconto; igual ao "base" quando não há promoção). Preço que só vale para
assinantes (PS Plus) não é usado. Mesmo formato do kabum.py.
"""
import html
import json
import re

BASE = "https://store.playstation.com"
TILE = re.compile(r'data-telemetry-meta="([^"]+)"[^>]*?href="(/pt-br/product/[^"]+)"', re.S)
IMG = re.compile(r'product-tile.*?src="(https://image\.api\.playstation\.com[^"?]+)', re.S)


class Blocked(Exception):
    pass


def _reais(txt):
    m = re.search(r"R\$\s*([\d.]+,\d{2})", txt or "")
    return float(m.group(1).replace(".", "").replace(",", ".")) if m else None


def parse(page_html):
    out, vistos = [], set()
    partes = page_html.split('class="psw-product-tile')[1:]
    for parte in partes:
        m = TILE.search(parte)
        if not m:
            continue
        try:
            meta = json.loads(html.unescape(m.group(1)))
        except ValueError:
            continue
        pr = meta.get("price") or {}
        code = meta.get("id")
        price = _reais(pr.get("discount"))
        base = _reais(pr.get("base"))
        if not code or code in vistos or not price or pr.get("isFree") or pr.get("isTiedToSubscription"):
            continue
        vistos.add(code)
        im = re.search(r'src="(https://image\.api\.playstation\.com[^"?]+)', parte)
        out.append({
            "code": code,
            "name": meta.get("name", "").strip(),
            "price": price,
            "list_price": max(base or 0, price),
            "seller": "PlayStation Store",
            "img": (im.group(1) + "?w=230") if im else None,
            "url": BASE + m.group(2),
            "available": True,
            "offer_ends": None,
        })
    return out


_pw = {}


def _browser():
    if "b" not in _pw:
        from playwright.sync_api import sync_playwright
        _pw["p"] = sync_playwright().start()
        _pw["b"] = _pw["p"].chromium.launch()
    return _pw["b"]


def fechar():
    if "b" in _pw:
        _pw["b"].close()
        _pw["p"].stop()
        _pw.clear()


def search(term):
    pg = _browser().new_page(locale="pt-BR")
    try:
        pg.goto(f"{BASE}/pt-br/search/{term.replace(' ', '%20')}", timeout=60000)
        try:
            pg.wait_for_selector(".psw-product-tile", timeout=30000)
        except Exception:  # noqa: BLE001 — sem resultados
            return []
        return parse(pg.content())
    finally:
        pg.close()
