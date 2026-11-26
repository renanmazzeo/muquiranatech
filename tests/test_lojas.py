"""Testes dos leitores de loja. Rodar: python -m unittest (na raiz do projeto)."""
import datetime as dt
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "collector"))
FIX = Path(__file__).with_name("fixtures")

import amazon  # noqa: E402
import kabum  # noqa: E402


def ler(nome):
    return (FIX / nome).read_text("utf-8")


class KabumOferta(unittest.TestCase):
    def test_oferta_ativa_vale(self):
        it = {i["code"]: i for i in kabum.parse(ler("kabum_busca.html"), at=2000000000)}
        self.assertEqual(it["1001"]["price"], 1100.0)  # preço da oferta, não os 1.400 sem oferta
        self.assertEqual(it["1001"]["offer_ends"], 4000000000)

    def test_oferta_fora_do_prazo_nao_vale(self):
        antes = {i["code"]: i for i in kabum.parse(ler("kabum_busca.html"), at=1600000000)}
        depois = {i["code"]: i for i in kabum.parse(ler("kabum_busca.html"), at=4100000000)}
        for it in (antes["1001"], depois["1001"]):
            self.assertEqual(it["price"], 1400.0)
            self.assertIsNone(it["offer_ends"])

    def test_sem_oferta(self):
        it = {i["code"]: i for i in kabum.parse(ler("kabum_busca.html"), at=2000000000)}["1002"]
        self.assertEqual(it["price"], 380.0)
        self.assertEqual(it["list_price"], 450.0)

    def test_caixa_aberta_fora(self):
        codes = {i["code"] for i in kabum.parse(ler("kabum_busca.html"))}
        self.assertNotIn("1004", codes)

    def test_pagina_sem_dados(self):
        self.assertEqual(kabum.parse("<html></html>"), [])


class Pick(unittest.TestCase):
    def setUp(self):
        self.items = kabum.parse(ler("kabum_busca.html"), at=2000000000)

    def codes(self, **kw):
        return [i["code"] for i in kabum.pick(self.items, **kw)]

    def test_vendedor_confiavel(self):
        self.assertNotIn("1003", self.codes())  # "Loja Qualquer" não é confiável
        self.assertIn("1003", self.codes(sellers=("KaBuM!", "Loja Qualquer")))

    def test_indisponivel_fora(self):
        self.assertNotIn("1005", self.codes())

    def test_must_ignora_acento_e_maiuscula(self):
        self.assertEqual(self.codes(must=["MONITOR", "polegadas"]), ["1001"])
        self.assertEqual(self.codes(must=["monitor", "ssd"]), [])

    def test_not(self):
        self.assertEqual(self.codes(exclude=["monitor"]), ["1002"])

    def test_limite(self):
        self.assertEqual(len(self.codes(limit=1)), 1)


class AmazonParse(unittest.TestCase):
    def test_ignora_patrocinado(self):
        nomes = [i["name"] for i in amazon.parse(ler("amazon_busca.html"))]
        self.assertEqual(nomes, ["Echo Dot 5a geração", "Kindle 16GB"])

    def test_precos(self):
        it = {i["code"]: i for i in amazon.parse(ler("amazon_busca.html"))}
        self.assertEqual(it["B000000001"]["price"], 349.0)
        self.assertEqual(it["B000000001"]["list_price"], 449.0)  # preço riscado
        self.assertEqual(it["B000000003"]["price"], 1099.9)
        self.assertEqual(it["B000000003"]["list_price"], 1099.9)  # sem preço riscado
        self.assertEqual(it["B000000001"]["url"], "https://www.amazon.com.br/dp/B000000001")

    def test_captcha(self):
        with self.assertRaises(amazon.Blocked):
            amazon.parse("<html><title>Digite os caracteres captcha</title></html>")


class Mesclar(unittest.TestCase):
    def test_mesclar_nao_duplica_nem_apaga_outra_loja(self):
        tmp = tempfile.mkdtemp()
        real, copia = os.path.join(tmp, "real.db"), os.path.join(tmp, "copia.db")
        os.environ["MUQ_DB"] = real
        import muq  # noqa: E402  (lê MUQ_DB ao ser importado)
        muq.DB = Path(real)
        hoje = dt.date.today().isoformat()

        def semear(caminho, linhas):
            muq.DB = Path(caminho)
            c = muq.db()
            for pid, loja, preco in linhas:
                c.execute("insert or replace into products(id,store,code,name,cat,url,img,seller,list_price,"
                          "first_seen,last_seen) values(?,?,?,?,?,?,?,?,?,?,?)",
                          (pid, loja, pid.split(":")[1], "Produto " + pid, "ssd", "u", "i", "s", preco, hoje, hoje))
                c.execute("insert or replace into prices values(?,?,?,?)", (pid, hoje, preco, "live"))
            c.commit()
            c.close()

        semear(real, [("amazon:A1", "amazon", 100.0), ("kabum:1", "kabum", 50.0)])
        semear(copia, [("kabum:1", "kabum", 45.0), ("kabum:2", "kabum", 70.0), ("amazon:A1", "amazon", 1.0)])
        muq.DB = Path(real)
        args = type("A", (), {"origem": copia, "lojas": "kabum", "wayback": False, "desde_dia": "2000-01-01"})()
        muq.cmd_mesclar(args)
        muq.cmd_mesclar(args)  # duas vezes: não pode duplicar
        c = sqlite3.connect(real)
        precos = dict(c.execute("select product_id, price from prices"))
        self.assertEqual(precos, {"amazon:A1": 100.0, "kabum:1": 45.0, "kabum:2": 70.0})
        self.assertEqual(c.execute("select count(*) from products").fetchone()[0], 3)


if __name__ == "__main__":
    unittest.main()
