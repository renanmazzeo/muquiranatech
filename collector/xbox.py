"""Leitura de jogos da Xbox Store (loja oficial da Microsoft, em reais).

As páginas só mostram os cartões depois que o JavaScript roda, por isso usa o navegador (Playwright).
`catalogo("browse")` abre a página pública "Jogos" (/pt-BR/games/browse, os mais populares primeiro) e clica em
"Carregar mais" como uma pessoa faria (25 jogos por clique). A busca (/search?q=) é proibida no robots.txt:
`search()` fica só para testes manuais e não é usada na coleta.
Cada cartão tem no `aria-label`: "Nome, Preço original R$X, à venda por R$Y". Sem desconto: "Nome, R$Y".
Cartão sem preço (jogo grátis, "Exibir jogo", só assinatura) é ignorado. Mesmo formato do kabum.py.
"""
import html
import re

BASE = "https://www.xbox.com"
CARD = re.compile(r'aria-label="([^"]*R\$[^"]*)"\s+href="(https://www\.xbox\.com/pt-BR/games/store/[^"]+)"')
IMG = re.compile(r'src="(https://store-images\.s-microsoft\.com/[^"?]+)')


class Blocked(Exception):
    pass


def _reais(txt):
    m = re.search(r"R\$\s*([\d.]+,\d{2})", txt or "")
    return float(m.group(1).replace(".", "").replace(",", ".")) if m else None


def parse(page_html):
    out, vistos = [], set()
    for parte in page_html.split("<li>")[1:]:
        m = CARD.search(parte)
        if not m:
            continue
        label = html.unescape(m.group(1))
        url = m.group(2)
        code = url.rstrip("/").rsplit("/", 1)[-1].upper()
        nome = re.split(r",\s*(?:Preço original|R\$)", label)[0].strip()
        if "à venda por" in label:
            original = _reais(label.split("Preço original", 1)[-1])
            price = _reais(label.split("à venda por", 1)[1])
        else:
            original = price = _reais(label.split(",", 1)[-1] if "," in label else label)
            original = price
        if not nome or code in vistos or not price:
            continue
        vistos.add(code)
        im = IMG.search(parte)
        out.append({
            "code": code,
            "name": nome,
            "price": price,
            "list_price": max(original or 0, price),
            "seller": "Xbox Store",
            "img": (im.group(1) + "?w=230") if im else None,
            "url": url,
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
        pg.goto(f"{BASE}/pt-BR/search?q={term.replace(' ', '%20')}", timeout=60000)
        try:
            # o menu do topo também tem links /games/store/ (escondidos): espere o cartão com preço
            pg.wait_for_selector('a[aria-label*="R$"][href*="/games/store/"]', state="attached", timeout=45000)
        except Exception:  # noqa: BLE001 — sem resultados
            pg.wait_for_timeout(3000)
        return parse(pg.content())
    finally:
        pg.close()


def catalogo(path="browse", cliques=16, pausa=3.5):
    """Jogos da página pública de navegação da loja, com preço (25 por clique em "Carregar mais")."""
    pg = _browser().new_page(locale="pt-BR")
    try:
        pg.goto(f"{BASE}/pt-BR/games/{path}", wait_until="load", timeout=90000)
        pg.wait_for_timeout(5000)
        btn = pg.locator("button:has-text('Carregar mais')")
        for _ in range(cliques):
            if not btn.count():
                break
            btn.first.scroll_into_view_if_needed()
            btn.first.click()
            pg.wait_for_timeout(int(pausa * 1000))
        return parse(pg.content())
    finally:
        pg.close()
