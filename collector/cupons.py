"""Cupons que aparecem na janela do produto (só de lojas que estão no site).

Duas fontes, juntadas no `exportar`:
- `data/cupons.json`: cupons cadastrados à mão (ex.: um cupom exclusivo que a loja mandou para o MuquiranaTech).
- `data/cupons-auto.json`: gerado pelo comando `cupons` a partir da API da Lomadee (precisa do LOMADEE_API_KEY).
  Só entram cupons de marcas ligadas a uma loja do site pela chave "lomadee" da loja na watchlist.

Formato de cada cupom (os campos com * são obrigatórios):
  loja*      chave da loja no site (ex.: "lenovo")
  codigo*    o código que o cliente cola no carrinho
  titulo*    a regra em português (ex.: "10% OFF em notebooks acima de R$ 3.000")
  ate        fim da validade (ISO 8601); sem ele, vale até ser apagado
  link       link para a loja (de afiliado); sem ele, o site usa o link do produto
  pct        desconto em % (só preencher quando vale para tudo o que o filtro pega)
  valor      desconto em reais (idem)
  minimo     compra mínima em reais para o desconto valer
  cat        lista de categorias do site em que vale (ex.: ["notebook"]); sem ela, vale para a loja toda
  palavras   lista de palavras que o nome do produto precisa ter (qualquer uma); sem ela, vale para todos
  fonte      "manual" ou "lomadee"
O "preço com cupom" só é calculado no site quando há `pct` ou `valor` (regra simples e segura).
"""
import datetime as dt
import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
MANUAL = ROOT / "data" / "cupons.json"
AUTO = ROOT / "data" / "cupons-auto.json"
API = "https://api.lomadee.com.br"


def _ler(arq):
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def validos(agora=None):
    """Cupons das duas fontes que ainda valem, sem repetir o mesmo código na mesma loja (o manual ganha)."""
    agora = agora or dt.datetime.now(dt.timezone.utc)
    out, vistos = [], set()
    for c in _ler(MANUAL) + _ler(AUTO):
        if not (c.get("loja") and c.get("codigo") and c.get("titulo")):
            continue
        if c.get("ate"):
            try:
                if dt.datetime.fromisoformat(c["ate"].replace("Z", "+00:00")) <= agora:
                    continue
            except ValueError:
                continue
        chave = (c["loja"], c["codigo"].upper())
        if chave in vistos:
            continue
        vistos.add(chave)
        out.append({k: v for k, v in c.items() if k in
                    ("loja", "codigo", "titulo", "ate", "link", "pct", "valor", "minimo", "cat", "palavras", "fonte")})
    return out


def _get(path, **params):
    time.sleep(1.2)  # limite da Lomadee: 60 por minuto
    r = requests.get(API + path, headers={"x-api-key": os.environ["LOMADEE_API_KEY"], "Accept": "application/json"},
                     params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def de_lomadee(marcas):
    """Cupons genéricos ativos das marcas {nome da marca na Lomadee (minúsculo): loja do site}."""
    out, pagina = [], 1
    nomes = {}
    while pagina <= 20:
        try:
            j = _get("/affiliate/campaigns", types="GenericCoupon", limit=20, page=pagina)
        except requests.HTTPError:
            if pagina == 1:
                raise
            break  # a Lomadee às vezes dá erro 500 numa página do meio: fica com as que vieram

        for x in j.get("data") or []:
            oid = x.get("organizationId")
            if oid not in nomes:
                b = _get(f"/affiliate/brands/{oid}")
                nomes[oid] = str(((b.get("data") or b) if isinstance(b, dict) else {}).get("name") or "").strip().lower()
            # nome igual, ou começando pelo nome da watchlist (razões sociais longas: "... Eletronicos Ltda")
            loja = marcas.get(nomes[oid]) or next((v for k, v in marcas.items() if nomes[oid].startswith(k)), None)
            if not loja or not x.get("code") or x.get("status") not in (None, "onTime"):
                continue
            links = [u for ch in x.get("channels") or [] for u in ch.get("shortUrls") or []]
            out.append({"loja": loja, "codigo": x["code"].strip(), "titulo": str(x.get("name") or "").strip(),
                        "ate": (x.get("period") or {}).get("endAt"), "link": links[0] if links else None,
                        "fonte": "lomadee"})
        if pagina >= ((j.get("meta") or {}).get("totalPages") or 1):
            break
        pagina += 1
    return out


def atualizar(lojas_cfg):
    """Regrava data/cupons-auto.json com os cupons da Lomadee. Sem a chave, não mexe em nada."""
    if not os.environ.get("LOMADEE_API_KEY"):
        print("Cupons: sem LOMADEE_API_KEY, mantendo os cupons automáticos de antes.")
        return
    marcas = {str(v["lomadee"]).lower(): k for k, v in lojas_cfg.items() if v.get("lomadee")}
    if not marcas:
        return
    try:
        novos = de_lomadee(marcas)
    except Exception as e:  # noqa: BLE001 — cupom nunca derruba a coleta
        print(f"Cupons: Lomadee falhou ({e}); mantendo os de antes.")
        return
    AUTO.write_text(json.dumps(novos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"Cupons: {len(novos)} da Lomadee para as lojas do site.")
