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
import mercadolivre  # noqa: E402
import steam  # noqa: E402
import kalunga  # noqa: E402
import playstation  # noqa: E402
import xbox  # noqa: E402
import samsung  # noqa: E402
import motorola  # noqa: E402
import lenovo  # noqa: E402
import cupons  # noqa: E402
import pcyes  # noqa: E402
import concordia  # noqa: E402
import xiaomi  # noqa: E402
import wayback  # noqa: E402
import categorias  # noqa: E402

# lojas que o coletor sabe ler (cada módulo tem search(termo) -> itens no mesmo formato)
LOJAS = {"kabum": kabum, "amazon": amazon, "steam": steam, "kalunga": kalunga, "playstation": playstation, "xbox": xbox, "samsung": samsung, "motorola": motorola, "lenovo": lenovo, "pcyes": pcyes, "concordia": concordia, "xiaomi": xiaomi, "ml": mercadolivre}

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
    create table if not exists wayback_done(key text primary key);
    """)
    cols = {r[1] for r in c.execute("pragma table_info(products)")}
    for col in ("offer_ends integer", "checked_at text", "parcelas text"):  # colunas novas em bancos antigos
        if col.split()[0] not in cols:
            c.execute(f"alter table products add column {col}")
    # preços ordenados por DIA (without rowid): a coleta de hoje só acrescenta páginas no fim do arquivo.
    # Ordenado por produto, cada coleta mexia no arquivo inteiro e o .db pesava muito mais no histórico do git.
    sql = (c.execute("select sql from sqlite_master where name='prices'").fetchone() or [""])[0]
    if "primary key(day" not in sql:
        c.executescript("""
        create table prices_novo(
          product_id text, day text, price real, source text,  -- source: live | wayback
          primary key(day, product_id, source)) without rowid;
        """)
        if sql:
            c.execute("insert into prices_novo select product_id, day, price, source from prices")
            c.execute("drop table prices")
        c.execute("alter table prices_novo rename to prices")
        c.commit()
        if sql:
            c.execute("vacuum")
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
        cfg = w["lojas"][loja]
        if loja == "ml" and not mercadolivre.configurado():
            print("== Mercado Livre: sem ML_CLIENT_ID/ML_CLIENT_SECRET, pulando (sem erro).")
            continue
        try:
            total = coletar_loja(c, loja, cfg, cfg.get("buscas", w["buscas"]), today, now, cfg.get("pausa", a.pausa))
        finally:
            # lojas com navegador (PlayStation, Xbox): fecha antes da próxima, senão a segunda não consegue abrir
            if hasattr(LOJAS[loja], "fechar"):
                LOJAS[loja].fechar()
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
            # "max_busca" da loja: quantos produtos aproveitar de cada página de busca, no mínimo (mesmo
            # número de acessos à loja, mais variedade de modelos e marcas)
            limite = max(q.get("max", 4), cfg.get("max_busca", 0))
            chosen = kabum.pick(mod.search(q["q"]), q.get("must", []), limite,
                                cfg["vendedores_confiaveis"], q.get("not", []) + cfg.get("not", []))
            if hasattr(mod, "refinar"):  # loja cuja lista de busca não traz o preço final: confere na ficha
                refinados = []
                for it in chosen:
                    time.sleep(pausa)
                    it = mod.refinar(it)
                    if it:
                        refinados.append(it)
                chosen = refinados
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
            salvar(c, loja, it, q["cat"], today, now)
            total += 1
        print(f"  {q['q']:<28} {len(chosen)} produtos")
        time.sleep(pausa)
    # catálogo: a categoria inteira da loja, só o que a própria loja vende (ver kabum.catalogo)
    if cfg.get("catalogo") and hasattr(mod, "catalogo"):
        evitar = [kabum.norm(w) for w in cfg.get("not", []) + cfg.get("catalogo_not", [])]
        for cat in cfg["catalogo"]:
            try:
                itens = mod.catalogo(cat["path"], pausa=pausa)
            except Exception as e:  # noqa: BLE001
                print(f"  ! catálogo {cat['path']}: {e}")
                continue
            n = 0
            for it in itens:
                nome = kabum.norm(it["name"])
                if not it["available"] or any(w in nome for w in evitar):
                    continue
                # "fixa": a categoria da própria loja já é a certa (ex.: Samsung, onde o nome começa pela marca)
                # ou a loja já diz a categoria do site no item (ex.: Xiaomi, pela categoria da própria loja)
                categoria = it.get("cat") or (cat["cat"] if cat.get("fixa") else
                                              categorias.classificar(it["name"], cat.get("cat", "perif")))
                salvar(c, loja, it, categoria, today, now)
                n += 1
            total += n
            print(f"  catálogo {cat['path']:<32} {n} produtos")
            time.sleep(pausa)
    return total


def salvar(c, loja, it, cat, today, now):
    """Grava o produto e o preço de hoje. A categoria só vale na 1ª vez (a de uma busca não é trocada)."""
    pid = f"{loja}:{it['code']}"
    c.execute("""insert into products
      (id,store,code,name,cat,url,img,seller,list_price,first_seen,last_seen,offer_ends,checked_at,parcelas)
      values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
      on conflict(id) do update set name=excluded.name, url=excluded.url, img=excluded.img,
      seller=excluded.seller, list_price=excluded.list_price, last_seen=excluded.last_seen,
      offer_ends=excluded.offer_ends, checked_at=excluded.checked_at, parcelas=excluded.parcelas""",
              (pid, loja, it["code"], it["name"], cat, it["url"], it["img"],
               it["seller"], it["list_price"], today, today, it["offer_ends"], now,
               json.dumps(it["parc"]) if it.get("parc") else None))
    c.execute("insert or replace into prices(product_id,day,price,source) values(?,?,?,?)",
              (pid, today, it["price"], "live"))


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
    # e também se o preço não foi conferido nas últimas 36 h (produto esgotado, saiu da busca, robô parado)
    recente = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=36)).isoformat(timespec="minutes")
    produtos, nomes = [], {k: v["nome"] for k, v in watchlist()["lojas"].items()}
    # todos os preços numa passada só (com milhares de produtos, uma consulta por produto ficava lenta)
    dias, vivo = {}, {}
    for pid, day, price, source in c.execute("select product_id, day, price, source from prices order by day"):
        d = dias.setdefault(pid, {})
        d[day] = min(price, d.get(day, price))
        if source == "live":
            vivo[pid] = price  # o último dia (ordem por dia) fica
    for pid, store, name, cat, url, img, seller, list_price, offer_ends, checked_at, parc in c.execute(
            "select id,store,name,cat,url,img,seller,list_price,offer_ends,checked_at,parcelas from products"
            " where last_seen>=? order by id",
            (cutoff,)).fetchall():
        hist = sorted(dias.get(pid, {}).items())
        cur = (vivo[pid],) if pid in vivo else None
        if not hist or not cur:
            continue
        if not checked_at or checked_at < recente:  # preço velho pode não bater com o da loja: fica fora do site
            continue
        produtos.append({
            "id": pid, "n": name, "cat": cat, "st": store, "url": url, "img": img,
            # vendido pela própria loja: o site escreve "Vendido e entregue por <loja>"
            "seller": None if store in kabum.norm(seller).replace(".com.br", "") else
            f"Vendido por {seller} · parceiro oficial {nomes[store]}",
            "full": list_price, "cur": cur[0], "hist": [[d, p] for d, p in hist],
            "at": checked_at,  # quando o preço de hoje foi visto na loja (UTC)
            "ends": offer_ends,  # fim da oferta relâmpago, se houver (epoch)
            "parc": json.loads(parc) if parc else None,  # parcelamento no cartão (collector/parcelas.py)
        })
    payload = {"gerado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"), "produtos": produtos,
               "cupons": cupons.validos()}  # cupons das lojas do site (ver collector/cupons.py)
    out = ROOT / "data.js"
    with open(out, "w", encoding="utf-8", newline="\n") as f:  # sempre LF, igual no Windows e no GitHub
        f.write("window.MUQ_DATA=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n")
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
    # cópia feita por um robô com código antigo pode não ter a coluna de parcelamento
    tem_parc = "parcelas" in {r[1] for r in c.execute("pragma o.table_info(products)")}
    c.execute(f"""insert into products(id,store,code,name,cat,url,img,seller,list_price,first_seen,last_seen,
                                       offer_ends,checked_at,parcelas)
        select id,store,code,name,cat,url,img,seller,list_price,first_seen,last_seen,offer_ends,checked_at,
               {"parcelas" if tem_parc else "null"}
        from o.products where store in ({marks})
        on conflict(id) do update set name=excluded.name, cat=excluded.cat, url=excluded.url, img=excluded.img,
          seller=excluded.seller, list_price=excluded.list_price, last_seen=max(last_seen, excluded.last_seen),
          first_seen=min(first_seen, excluded.first_seen), offer_ends=excluded.offer_ends,
          checked_at=max(coalesce(checked_at,''), coalesce(excluded.checked_at,'')),
          parcelas=case when coalesce(excluded.checked_at,'') >= coalesce(checked_at,'') then excluded.parcelas
                        else parcelas end""", lojas)
    n = c.execute(f"""insert or replace into prices select x.* from o.prices x
        join o.products p on p.id=x.product_id
        where p.store in ({marks}) and x.source='live' and x.day>=?""", (*lojas, a.desde_dia)).rowcount
    w = 0
    if a.wayback:
        w = c.execute("insert or ignore into prices select * from o.prices where source='wayback'").rowcount
        c.execute("insert or ignore into wayback_done select * from o.wayback_done")
    c.commit()
    print(f"Mesclado de {a.origem}: lojas {', '.join(lojas)} · {n} preços ao vivo · {w} preços da Wayback")


def cmd_testar(a):
    """Roda um pedido de sondagem (ver sondar.py) e grava o resultado em JSON.

    O agente autônomo usa isto para descobrir se uma loja funciona pela rede do GitHub
    (workflow sondar.yml) ou pelo PC do dono (coletar-pc.ps1 lê docs/sondagens/pedido-pc.json).
    """
    import sondar
    pedido = json.loads(Path(a.origem).read_text("utf-8"))
    print(f"Sondagem {pedido.get('id')} ({a.onde}): {len(pedido.get('testes', []))} testes")
    res = {"id": pedido.get("id"), "onde": a.onde,
           "quando": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
           "resultados": sondar.rodar(pedido, LOJAS, pausa=a.pausa)}
    if a.saida:
        Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
        with open(a.saida, "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
            f.write("\n")
    ok = sum(1 for r in res["resultados"] if r.get("funcionou"))
    print(f"{ok} de {len(res['resultados'])} testes funcionaram")


def lojas_do(onde):
    """Lojas que este robô coleta: "onde" na watchlist ("github", o padrão, ou "pc")."""
    return [k for k, v in watchlist()["lojas"].items() if v.get("onde", "github") == onde and k in LOJAS]


def main():
    p = argparse.ArgumentParser(description="Coletor de preços do MuquiranaTech")
    p.add_argument("comando", choices=["coletar", "historico", "exportar", "tudo", "mesclar", "testar", "lojas", "cupons"])
    p.add_argument("origem", nargs="?", help="mesclar: banco (cópia) de onde vêm os dados novos; "
                                             "testar: arquivo do pedido; lojas: github ou pc")
    p.add_argument("--saida", help="testar: arquivo JSON onde gravar o resultado")
    p.add_argument("--onde", default="github", help="testar: onde o teste está rodando (github ou pc)")
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
    if a.comando == "testar":
        cmd_testar(a)
    if a.comando == "lojas":  # usado pelos robôs: imprime as lojas daquele lugar, separadas por vírgula
        print(",".join(lojas_do(a.origem or "github")))
    if a.comando == "cupons":  # cupons automáticos (Lomadee) → data/cupons-auto.json
        cupons.atualizar(watchlist()["lojas"])
    if a.comando in ("exportar", "tudo"):
        cmd_exportar(a)


if __name__ == "__main__":
    main()
