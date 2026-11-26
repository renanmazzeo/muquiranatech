"""MuquiranaTech — coletor de preços.

Uso (na pasta muquiranatech):
  .venv\\Scripts\\python collector\\muq.py coletar     preço de hoje nas lojas
  .venv\\Scripts\\python collector\\muq.py historico   completa o passado com a Wayback Machine
  .venv\\Scripts\\python collector\\muq.py exportar    gera data.js para o site
  .venv\\Scripts\\python collector\\muq.py tudo        coletar + exportar
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import amazon  # noqa: E402
import kabum  # noqa: E402
import wayback  # noqa: E402

# lojas que o coletor sabe ler (cada módulo tem search(termo) -> itens no mesmo formato)
LOJAS = {"kabum": kabum, "amazon": amazon}

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "muquirana.db"
# MUQ_DB: coletar numa cópia do banco e depois "mesclar" no banco real (ver cmd_mesclar)
if os.environ.get("MUQ_DB"):
    DB = Path(os.environ["MUQ_DB"]).resolve()
WATCH = Path(__file__).with_name("watchlist.json")


def db():
    DB.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB)
    c.executescript("""
    create table if not exists products(
      id text primary key, store text, code text, name text, cat text, url text, img text,
      seller text, list_price real, first_seen text, last_seen text);
    create table if not exists prices(
      product_id text, day text, price real, source text,  -- source: live | wayback
      primary key(product_id, day, source));
    create table if not exists wayback_done(key text primary key);
    """)
    cols = {r[1] for r in c.execute("pragma table_info(products)")}
    for col in ("offer_ends integer", "checked_at text"):  # colunas novas em bancos antigos
        if col.split()[0] not in cols:
            c.execute(f"alter table products add column {col}")
    return c


BRT = dt.timezone(dt.timedelta(hours=-3))  # Brasília (sem horário de verão desde 2019)


def hoje():
    """Data de hoje no Brasil (o robô do GitHub roda em UTC)."""
    return dt.datetime.now(BRT).date()


def watchlist():
    return json.loads(WATCH.read_text("utf-8"))


def cmd_coletar(a):
    c, today = db(), hoje().isoformat()
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
    w = watchlist()
    lojas = a.lojas.split(",") if a.lojas else list(w["lojas"])
    for loja in lojas:
        total = coletar_loja(c, loja, w["lojas"][loja], w["buscas"], today, now, a.pausa)
        c.commit()
        print(f"== {w['lojas'][loja]['nome']}: {total} preços de hoje salvos.")


def coletar_loja(c, loja, cfg, buscas, today, now, pausa):
    mod, total, erros = LOJAS[loja], 0, 0
    print(f"== {cfg['nome']}")
    for base in buscas:
        q = {**base, **base.get(loja, {})}  # ajustes só desta loja (ex.: "amazon": {"must": [...]})
        if q.get("skip"):
            continue
        try:
            chosen = kabum.pick(mod.search(q["q"]), q.get("must", []), q.get("max", 4),
                                cfg["vendedores_confiaveis"], q.get("not", []) + cfg.get("not", []))
        except getattr(mod, "Blocked", ()) as e:  # a loja pediu captcha: tenta de novo na próxima rodada
            print(f"  ! {cfg['nome']} bloqueou ({e}); parando esta loja por agora")
            break
        except Exception as e:  # noqa: BLE001 — uma busca com erro não derruba as outras
            print(f"  ! {q['q']}: {e}")
            erros += 1
            if erros >= 10:
                print(f"  ! erros demais em {cfg['nome']}; parando esta loja por agora")
                break
            continue
        for it in chosen:
            pid = f"{loja}:{it['code']}"
            c.execute("""insert into products
              (id,store,code,name,cat,url,img,seller,list_price,first_seen,last_seen,offer_ends,checked_at)
              values(?,?,?,?,?,?,?,?,?,?,?,?,?)
              on conflict(id) do update set name=excluded.name, url=excluded.url, img=excluded.img,
              seller=excluded.seller, list_price=excluded.list_price, last_seen=excluded.last_seen,
              offer_ends=excluded.offer_ends, checked_at=excluded.checked_at""",
                      (pid, loja, it["code"], it["name"], q["cat"], it["url"], it["img"],
                       it["seller"], it["list_price"], today, today, it["offer_ends"], now))
            c.execute("insert or replace into prices values(?,?,?,?)", (pid, today, it["price"], "live"))
            total += 1
        print(f"  {q['q']:<28} {len(chosen)} produtos")
        time.sleep(pausa)
    return total


def cmd_historico(a):
    c, wl = db(), watchlist()
    w = {**wl["lojas"]["kabum"], "buscas": wl["buscas"]}  # histórico da Wayback: só KaBuM! por enquanto
    known = {r[0] for r in c.execute("select code from products where store='kabum'")}
    if not known:
        print('Nenhum produto ainda. Rode "coletar" primeiro.')
        return
    pages = ["kabum.com.br/" + p for p in w["wayback_paginas"]]
    pages += ["kabum.com.br/busca/" + q["q"] for q in w["buscas"]]
    d0 = hoje()
    m = d0.year * 12 + d0.month - 1 - a.meses
    desde = a.desde or f"{m // 12}{m % 12 + 1:02d}"
    print(f"Histórico desde {desde[:4]}/{desde[4:] or '01'} ({a.meses} meses)")
    done = {r[0] for r in c.execute("select key from wayback_done")}
    todo = []
    for url in pages:
        try:
            snaps = wayback.snapshots(url, since=desde, per_month=a.por_mes)
        except Exception as e:  # noqa: BLE001
            print(f"! {url}: {e}")
            continue
        new = [s for s in snaps if f"{s[0]} {s[1]}" not in done]
        print(f"{url}: {len(snaps)} cópias ({len(new)} novas)")
        todo += new
        time.sleep(a.pausa)
    # mais recentes primeiro: o passado próximo importa mais (ex.: Black Fraude olha os últimos 90 dias)
    todo.sort(key=lambda s: s[0], reverse=True)
    deadline = time.monotonic() + a.max_minutos * 60
    print(f"{len(todo)} cópias para baixar (limite de {a.max_minutos:g} min; o resto fica para a próxima vez)")
    for n, (ts, original) in enumerate(todo, 1):
        if time.monotonic() > deadline:
            print(f"Tempo esgotado: {len(todo) - n + 1} cópias ficam para a próxima execução.")
            break
        try:
            html = wayback.fetch(ts, original)
        except Exception as e:  # noqa: BLE001
            print(f"   ! {ts} {original}: {e}")
            continue
        day, hits = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}", 0
        for it in kabum.parse(html, at=wayback.epoch(ts)):
            if it["code"] in known:
                c.execute("insert or replace into prices values(?,?,?,?)",
                          ("kabum:" + it["code"], day, it["price"], "wayback"))
                hits += 1
        c.execute("insert or ignore into wayback_done values(?)", (f"{ts} {original}",))
        c.commit()
        print(f"   [{n}/{len(todo)}] {day} {original}: {hits} preços dos nossos produtos")
        time.sleep(a.pausa)


def cmd_exportar(a):
    c = db()
    cutoff = (hoje() - dt.timedelta(days=7)).isoformat()  # some do site se a loja parou de listar
    produtos = []
    for pid, store, name, cat, url, img, seller, list_price, offer_ends, checked_at in c.execute(
            "select id,store,name,cat,url,img,seller,list_price,offer_ends,checked_at from products"
            " where last_seen>=? order by id",
            (cutoff,)).fetchall():
        hist = c.execute("select day, min(price) from prices where product_id=? group by day order by day",
                         (pid,)).fetchall()
        cur = c.execute("select price from prices where product_id=? and source='live' order by day desc limit 1",
                        (pid,)).fetchone()
        if not hist or not cur:
            continue
        produtos.append({
            "id": pid, "n": name, "cat": cat, "st": store, "url": url, "img": img,
            # vendido pela própria loja: o site escreve "Vendido e entregue por <loja>"
            "seller": None if store in kabum.norm(seller).replace(".com.br", "") else
            f"Vendido por {seller} · parceiro oficial {watchlist()['lojas'][store]['nome']}",
            "full": list_price, "cur": cur[0], "hist": [[d, p] for d, p in hist],
            "at": checked_at,  # quando o preço de hoje foi visto na loja (UTC)
            "ends": offer_ends,  # fim da oferta relâmpago, se houver (epoch)
        })
    payload = {"gerado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"), "produtos": produtos}
    out = ROOT / "data.js"
    out.write_text("window.MUQ_DATA=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   "utf-8")
    print(f"{len(produtos)} produtos exportados para {out.name}")


def cmd_mesclar(a):
    """Junta no banco real só o que uma coleta feita numa cópia (a.origem) produziu.

    Dois robôs coletam ao mesmo tempo (GitHub: KaBuM!; PC do dono: Amazon). Cada um coleta numa cópia
    e, logo antes do push, faz git pull e mescla aqui só as linhas das lojas dele. Assim um nunca apaga
    a coleta do outro, o que aconteceria se o git escolhesse um dos dois arquivos .db inteiro.
    """
    c = db()
    c.execute("attach database ? as o", (str(Path(a.origem).resolve()),))
    lojas = a.lojas.split(",") if a.lojas else [r[0] for r in c.execute("select distinct store from o.products")]
    marks = ",".join("?" * len(lojas))
    c.execute(f"""insert into products(id,store,code,name,cat,url,img,seller,list_price,first_seen,last_seen,
                                       offer_ends,checked_at)
        select id,store,code,name,cat,url,img,seller,list_price,first_seen,last_seen,offer_ends,checked_at
        from o.products where store in ({marks})
        on conflict(id) do update set name=excluded.name, cat=excluded.cat, url=excluded.url, img=excluded.img,
          seller=excluded.seller, list_price=excluded.list_price, last_seen=max(last_seen, excluded.last_seen),
          first_seen=min(first_seen, excluded.first_seen), offer_ends=excluded.offer_ends,
          checked_at=max(coalesce(checked_at,''), coalesce(excluded.checked_at,''))""", lojas)
    n = c.execute(f"""insert or replace into prices select x.* from o.prices x
        join o.products p on p.id=x.product_id
        where p.store in ({marks}) and x.source='live' and x.day>=?""", (*lojas, a.desde_dia)).rowcount
    w = 0
    if a.wayback:
        w = c.execute("insert or ignore into prices select * from o.prices where source='wayback'").rowcount
        c.execute("insert or ignore into wayback_done select * from o.wayback_done")
    c.commit()
    print(f"Mesclado de {a.origem}: lojas {', '.join(lojas)} · {n} preços ao vivo · {w} preços da Wayback")


def main():
    p = argparse.ArgumentParser(description="Coletor de preços do MuquiranaTech")
    p.add_argument("comando", choices=["coletar", "historico", "exportar", "tudo", "mesclar"])
    p.add_argument("origem", nargs="?", help="mesclar: banco (cópia) de onde vêm os dados novos")
    p.add_argument("--wayback", action="store_true", help="mesclar: incluir também o histórico da Wayback")
    p.add_argument("--desde-dia", default=(dt.datetime.now(BRT).date() - dt.timedelta(days=1)).isoformat(),
                   help="mesclar: preços ao vivo a partir deste dia (padrão: ontem)")
    p.add_argument("--pausa", type=float, default=2.0, help="segundos entre requisições (seja gentil)")
    p.add_argument("--lojas", help="só estas lojas, separadas por vírgula (ex.: kabum,amazon)")
    p.add_argument("--meses", type=int, default=12, help="histórico Wayback dos últimos N meses (padrão: 12)")
    p.add_argument("--desde", help="ou a partir deste ano/mês exato (AAAA ou AAAAMM)")
    p.add_argument("--por-mes", type=int, default=2, help="cópias da Wayback por mês e por página")
    p.add_argument("--max-minutos", type=float, default=1e9,
                   help="para o histórico depois de N minutos, salvando o que já baixou")
    a = p.parse_args()
    if a.comando in ("coletar", "tudo"):
        cmd_coletar(a)
    if a.comando == "historico":
        cmd_historico(a)
    if a.comando == "mesclar":
        cmd_mesclar(a)
    if a.comando in ("exportar", "tudo"):
        cmd_exportar(a)


if __name__ == "__main__":
    main()
