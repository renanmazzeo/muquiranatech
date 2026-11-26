"""Lista produtos suspeitos do data.js (só leitura, não altera nada).
Uso: python collector/revisar.py [data.js]"""
import json, re, statistics, sys, unicodedata
from collections import defaultdict

ACESSORIOS = ("capa", "pelicula", "película", "suporte", "cabo", "pilha", "carregador", "adaptador")
APARELHOS = ("celular", "smartphone", "tv", "notebook", "console", "monitor", "tablet")


def carregar(caminho="data.js"):
    t = open(caminho, encoding="utf-8").read()
    return json.loads(t[t.index("{"):t.rindex("}") + 1])["produtos"]


def sem_acento(s):
    return unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()


def revisar(produtos):
    por_cat = defaultdict(list)
    for p in produtos:
        if p.get("cur"):
            por_cat[p.get("cat")].append(p["cur"])
    med = {c: statistics.median(v) for c, v in por_cat.items() if len(v) >= 5}
    achados = []
    for p in produtos:
        nome = sem_acento(p["n"]); cat = p.get("cat"); cur = p.get("cur") or 0
        m = med.get(cat)
        if m and cur and (cur < 0.25 * m or cur > 4 * m):
            achados.append(("preço fora da mediana", p, f"R$ {cur:.2f} vs mediana R$ {m:.2f}"))
        if cat in APARELHOS and any(re.search(r"\b" + sem_acento(a) + r"\b", nome) for a in ACESSORIOS):
            achados.append(("acessório em categoria de aparelho", p, ""))
    return achados


if __name__ == "__main__":
    ach = revisar(carregar(*sys.argv[1:2]))
    from collections import Counter
    print(dict(Counter((m, p["st"]) for m, p, _ in ach)))
    for motivo, p, extra in ach[:80]:
        print(f"[{motivo}] {p['id']} · {p['cat']} · {p['n'][:70]} {extra}")
    print(f"{len(ach)} suspeitos (mostrando até 80)")
