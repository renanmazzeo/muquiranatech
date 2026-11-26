"""Sondagem de lojas: "esta loja responde para o nosso robô, e de que jeito?".

Usado pelo agente autônomo para descobrir um caminho que funcione para cada loja, tanto na rede do GitHub
quanto no PC do dono (que tem IP residencial e às vezes passa onde o GitHub é bloqueado).

Um pedido é um JSON assim (ver `muq.py testar`):
{
  "id": "2026-11-26-magalu",            # muda o id para pedir um teste novo
  "testes": [
    {"nome": "magalu-api",       "url": "https://...", "modo": "requests"},
    {"nome": "magalu-navegador", "url": "https://...", "modo": "playwright"},
    {"nome": "amazon-coletor",   "loja": "amazon", "q": "echo-dot"}   # usa o coletor pronto da loja
  ]
}
Modos: "requests" (rápido) e "playwright" (navegador Chromium de verdade; precisa do pacote playwright).
"""
import re
import time

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
}
PRECO = re.compile(r"R\$\s?(?:&nbsp;|\xa0)?\s?\d{1,3}(?:\.\d{3})*,\d{2}")
BLOQUEIO = re.compile(r"captcha|are you a robot|access denied|acesso negado|cf-chl|challenge-platform|"
                      r"verifique se você é humano|px-captcha|perimeterx|datadome", re.I)


def _resumo(status, texto, extra=None):
    precos = PRECO.findall(texto)
    titulo = re.search(r"<title[^>]*>(.*?)</title>", texto, re.S | re.I)
    r = {
        "status": status,
        "tamanho": len(texto),
        "precos_na_pagina": len(precos),
        "exemplos_de_preco": [p.replace("\xa0", " ").replace("&nbsp;", " ") for p in precos[:5]],
        "bloqueio_detectado": bool(BLOQUEIO.search(texto[:200000])),
        "titulo": re.sub(r"\s+", " ", titulo.group(1)).strip()[:120] if titulo else None,
        "json": texto.lstrip()[:1] in "[{",
    }
    # funcionou = respondeu 200, sem cara de bloqueio, e com preços (ou JSON com conteúdo)
    r["funcionou"] = status == 200 and not r["bloqueio_detectado"] and (len(precos) >= 3 or
                                                                         (r["json"] and len(texto) > 500))
    if extra:
        r.update(extra)
    return r


def _enxugar(html):
    """Tira estilos, SVGs e scripts sem preço, para sobrar a estrutura dos produtos."""
    html = re.sub(r"<style.*?</style>|<svg.*?</svg>|<!--.*?-->", "", html, flags=re.S | re.I)
    return re.sub(r"<script(?![^>]*(?:ld\+json|__NEXT_DATA__))[^>]*>(?:(?!</script>).)*</script>",
                  lambda m: m.group(0) if re.search(r"price|preco|preço", m.group(0), re.I) and len(m.group(0)) < 60000 else "",
                  html, flags=re.S | re.I)


def por_requests(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    return _resumo(r.status_code, r.text, {"url_final": r.url, "_html": r.text})


def por_navegador(url):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"funcionou": False, "erro": "playwright não instalado"}
    with sync_playwright() as p:
        nav = p.chromium.launch(headless=True)
        pag = nav.new_page(locale="pt-BR", user_agent=HEADERS["User-Agent"],
                           viewport={"width": 1366, "height": 900})
        resp = pag.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            pag.wait_for_load_state("networkidle", timeout=20000)
        except Exception:  # noqa: BLE001 — páginas com anúncios nunca ficam "quietas"; seguimos assim mesmo
            pass
        pag.mouse.wheel(0, 2500)  # algumas lojas só carregam os produtos depois de rolar
        time.sleep(3)
        html = pag.content()
        status = resp.status if resp else 0
        url_final = pag.url
        nav.close()
    return _resumo(status, html, {"url_final": url_final, "_html": html})


def por_coletor(loja, termo, lojas):
    itens = lojas[loja].search(termo)
    return {
        "funcionou": bool(itens),
        "itens": len(itens),
        "exemplos": [{"nome": i["name"][:70], "preco": i["price"], "vendedor": i.get("seller")} for i in itens[:5]],
    }


def rodar(pedido, lojas, pausa=3.0):
    resultados = []
    for t in pedido.get("testes", []):
        r = {"nome": t.get("nome"), "modo": t.get("modo") or ("coletor" if t.get("loja") else "requests"),
             "url": t.get("url"), "loja": t.get("loja"), "q": t.get("q")}
        try:
            if t.get("loja"):
                r.update(por_coletor(t["loja"], t["q"], lojas))
            elif t.get("modo") == "playwright":
                r.update(por_navegador(t["url"]))
            else:
                r.update(por_requests(t["url"]))
            html = r.pop("_html", None)
            if t.get("guardar") and html:  # guarda a página (até 400 KB) para o agente montar o coletor da loja
                import os
                pasta = os.environ.get("SONDAR_HTML", "docs/sondagens/html")
                os.makedirs(pasta, exist_ok=True)
                with open(os.path.join(pasta, f"{t['nome']}.html"), "w", encoding="utf-8") as f:
                    f.write(_enxugar(html)[:400000])
        except Exception as e:  # noqa: BLE001 — o erro é o próprio resultado do teste
            r.update({"funcionou": False, "erro": f"{type(e).__name__}: {e}"[:300]})
        resultados.append(r)
        print(f"  {'OK ' if r.get('funcionou') else 'NÃO'} {r['nome']}: "
              f"{r.get('status', '')} {r.get('erro', '')} precos={r.get('precos_na_pagina', r.get('itens', ''))}")
        time.sleep(pausa)
    return resultados
