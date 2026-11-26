"""Amazon Brasil: página de busca filtrada para "vendido e entregue pela Amazon.com.br".

O filtro rh=p_6:<id do vendedor> deixa só produtos da própria Amazon (nada de marketplace).
Anúncios patrocinados são ignorados: eles nem sempre respeitam o filtro de vendedor.
Devolve itens no mesmo formato do kabum.py, para o resto do coletor tratar as lojas igual.
"""
import html as htmllib
import re
import time

import requests

BASE = "https://www.amazon.com.br"
AMAZON_SELLER = "A1ZZFT5FULY4LN"  # Amazon.com.br
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class Blocked(Exception):
    """A Amazon pediu captcha: parar a loja nesta rodada em vez de insistir."""


def _brl(s):
    s = htmllib.unescape(s or "").replace("\xa0", " ")
    m = re.search(r"([\d.]+,\d{2})", s)
    return float(m.group(1).replace(".", "").replace(",", ".")) if m else None


def parse(page):
    if "captcha" in page[:30000].lower() and "s-search-result" not in page:
        raise Blocked("captcha")
    starts = [m.start() for m in re.finditer(r'data-component-type="s-search-result"', page)]
    out, seen = [], set()
    for i, pos in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(page)
        head = page[max(0, pos - 800):pos]
        blk = page[pos:end]
        asin = re.findall(r'data-asin="(\w{10})"', head)
        if not asin or asin[-1] in seen:
            continue
        if re.search(r"AdHolder|puis-sponsored|Patrocinado", blk[:6000]):
            continue
        t = re.search(r"<h2[^>]*>(.*?)</h2>", blk, re.S)
        name = htmllib.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip() if t else ""
        # preço atual: primeiro a-price que não é o riscado (a-text-price)
        price = None
        for m in re.finditer(r'<span class="a-price([^"]*)"[^>]*>\s*<span class="a-offscreen">([^<]+)<', blk):
            if "a-text-price" not in m.group(1):
                price = _brl(m.group(2))
                break
        if not name or not price:
            continue
        lp = re.search(r'a-text-price[^"]*"[^>]*>\s*<span class="a-offscreen">([^<]+)<', blk)
        img = re.search(r'class="s-image"[^>]*src="([^"]+)"', blk) or re.search(r'src="([^"]+)"[^>]*class="s-image"', blk)
        seen.add(asin[-1])
        out.append({
            "code": asin[-1],
            "name": re.sub(r"\s+", " ", name),
            "price": round(price, 2),
            "list_price": round(max(price, _brl(lp.group(1)) or 0), 2) if lp else round(price, 2),
            "seller": "Amazon.com.br",
            "img": img.group(1) if img else None,
            "url": f"{BASE}/dp/{asin[-1]}",
            "available": True,
            "offer_ends": None,
        })
    return out


_session = None


def _get(url, **kw):
    """Uma sessão com cookies (como um navegador) e paciência: a Amazon responde 503 a quem pede rápido demais."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(HEADERS)
        try:
            _session.get(BASE, timeout=30)  # pega os cookies da página inicial
        except requests.RequestException:
            pass
    for espera in (0, 60):
        time.sleep(espera)
        r = _session.get(url, timeout=30, **kw)
        if r.status_code != 503:
            r.raise_for_status()
            return r
    raise Blocked("HTTP 503")


def search(term):
    r = _get(f"{BASE}/s", params={"k": term.replace("-", " "), "rh": f"p_6:{AMAZON_SELLER}"})
    return parse(r.text)
