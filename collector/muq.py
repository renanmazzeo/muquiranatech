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
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kabum  # noqa: E402
import wayback  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "muquirana.db"
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
    return c


def watchlist():
    return json.loads(WATCH.read_text("utf-8"))


def cmd_coletar(a):
    c, today, total = db(), dt.date.today().isoformat(), 0
    w = watchlist()["kabum"]
    for q in w["buscas"]:
        try:
            chosen = kabum.pick(kabum.search(q["q"]), q.get("must", []), q.get("max", 4),
                                w["vendedores_confiaveis"], q.get("not", []))
        except Exception as e:  # noqa: BLE001 — uma busca com erro não derruba as outras
            print(f"  ! {q['q']}: {e}")
            continue
        for it in chosen:
            pid = "kabum:" + it["code"]
            c.execute("""insert into products values(?,?,?,?,?,?,?,?,?,?,?)
              on conflict(id) do update set name=excluded.name, url=excluded.url, img=excluded.img,
              seller=excluded.seller, list_price=excluded.list_price, last_seen=excluded.last_seen""",
                      (pid, "kabum", it["code"], it["name"], q["cat"], it["url"], it["img"],
                       it["seller"], it["list_price"], today, today))
            c.execute("insert or replace into prices values(?,?,?,?)", (pid, today, it["price"], "live"))
            total += 1
        print(f"  {q['q']:<28} {len(chosen)} produtos")
        time.sleep(a.pausa)
    c.commit()
    print(f"{total} preços de hoje salvos.")


def cmd_historico(a):
    c, w = db(), watchlist()["kabum"]
    known = {r[0] for r in c.execute("select code from products where store='kabum'")}
    if not known:
        print('Nenhum produto ainda. Rode "coletar" primeiro.')
        return
    pages = ["kabum.com.br/" + p for p in w["wayback_paginas"]]
    pages += ["kabum.com.br/busca/" + q["q"] for q in w["buscas"]]
    hoje = dt.date.today()
    m = hoje.year * 12 + hoje.month - 1 - a.meses
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
        for it in kabum.parse(html):
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
    cutoff = (dt.date.today() - dt.timedelta(days=7)).isoformat()  # some do site se a loja parou de listar
    produtos = []
    for pid, store, name, cat, url, img, seller, list_price in c.execute(
            "select id,store,name,cat,url,img,seller,list_price from products where last_seen>=? order by id",
            (cutoff,)).fetchall():
        hist = c.execute("select day, min(price) from prices where product_id=? group by day order by day",
                         (pid,)).fetchall()
        cur = c.execute("select price from prices where product_id=? and source='live' order by day desc limit 1",
                        (pid,)).fetchone()
        if not hist or not cur:
            continue
        produtos.append({
            "id": pid, "n": name, "cat": cat, "st": store, "url": url, "img": img,
            "seller": None if "kabum" in kabum.norm(seller) else f"Vendido por {seller} · parceiro oficial KaBuM!",
            "full": list_price, "cur": cur[0], "hist": [[d, p] for d, p in hist],
        })
    payload = {"gerado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"), "produtos": produtos}
    out = ROOT / "data.js"
    out.write_text("window.MUQ_DATA=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   "utf-8")
    print(f"{len(produtos)} produtos exportados para {out.name}")


def main():
    p = argparse.ArgumentParser(description="Coletor de preços do MuquiranaTech")
    p.add_argument("comando", choices=["coletar", "historico", "exportar", "tudo"])
    p.add_argument("--pausa", type=float, default=2.0, help="segundos entre requisições (seja gentil)")
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
    if a.comando in ("exportar", "tudo"):
        cmd_exportar(a)


if __name__ == "__main__":
    main()
