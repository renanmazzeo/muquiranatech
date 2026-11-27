"""Parcelamento no cartão, no formato que vai para o site: {"n": 10, "v": 117.64, "total": 1176.40, "juros": false}.

Cada loja informa de um jeito; aqui ficam as funções comuns. Sem informação confiável, devolve None e o site
não mostra nada (nunca inventar parcelamento).
"""
import re


def montar(n, v, total=None, juros=None, preco_cartao=None):
    """Monta o parcelamento. `juros` explícito vale; senão compara o total parcelado com o preço no cartão à vista."""
    try:
        n, v = int(n), round(float(v), 2)
    except (TypeError, ValueError):
        return None
    if n < 2 or v <= 0:
        return None
    total = round(float(total), 2) if total else round(n * v, 2)
    if juros is None:
        if not preco_cartao:
            return None  # sem referência não dá para afirmar "sem juros"
        juros = total > float(preco_cartao) + max(1.0, 0.01 * float(preco_cartao))
    return {"n": n, "v": v, "total": total, "juros": bool(juros)}


def de_texto(txt, preco_cartao):
    """Ex.: KaBuM! "10x de R$ 117,64"."""
    m = re.search(r"(\d+)\s*x\s*de\s*R\$\s*([\d.]+,\d{2})", txt or "")
    if not m:
        return None
    return montar(m.group(1), m.group(2).replace(".", "").replace(",", "."), preco_cartao=preco_cartao)


CARTOES = ("visa", "mastercard", "elo", "american express", "hipercard")


def vtex(installments):
    """Lojas VTEX (Samsung, Motorola): o maior número de parcelas sem juros num cartão comum;
    se não houver nenhuma sem juros, o maior parcelamento com juros."""
    ops = [i for i in installments or []
           if str(i.get("PaymentSystemName", "")).lower() in CARTOES and (i.get("NumberOfInstallments") or 0) >= 2]
    if not ops:
        return None
    sem = [i for i in ops if not i.get("InterestRate")]
    i = max(sem or ops, key=lambda x: x["NumberOfInstallments"])
    return montar(i["NumberOfInstallments"], i["Value"], i.get("TotalValuePlusInterestRate"), juros=not sem)
