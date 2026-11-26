"""Testes do leitor da Kalunga (HTML de exemplo: 3 blocos reais de uma busca, sem estilos e scripts)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collector"))
import kabum  # noqa: E402
import kalunga  # noqa: E402

HTML = (Path(__file__).parent / "fixtures" / "kalunga_busca.html").read_text("utf-8")


class Kalunga(unittest.TestCase):
    def test_parse(self):
        itens = {i["code"]: i for i in kalunga.parse(HTML)}
        self.assertEqual(len(itens), 3)
        self.assertEqual(itens["442311"]["price"], 28.5)  # sem "De:"
        self.assertEqual(itens["442311"]["list_price"], 28.5)
        self.assertEqual(itens["464357"]["price"], 44.9)  # com "De: R$ 59,90"
        self.assertEqual(itens["464357"]["list_price"], 59.9)
        self.assertEqual(itens["442535"]["price"], 223.0)  # "à vista" dentro do preço
        self.assertTrue(itens["442311"]["url"].startswith("https://www.kalunga.com.br/prod/"))
        self.assertEqual(itens["442311"]["seller"], "Kalunga")

    def test_pick_exclui_mousepad(self):
        escolhidos = kabum.pick(kalunga.parse(HTML), ["mouse"], 5, ["Kalunga"], ["pad"])
        self.assertEqual({i["code"] for i in escolhidos}, {"442311", "442535"})

    def test_preco_da_ficha(self):
        vista = '<span id="hfprecovista">R$ 218,41</span><small>à vista</small> "price": 229.9'
        unico = '<span id="hfprecovenda">R$ 28,50</span> "price": 28.5'
        sem_cabecalho = '<input id="txtPrecoVista" value="R$ 1.044,05"> "price": 1100'
        self.assertEqual(kalunga.preco_ficha(vista), 218.41)
        self.assertEqual(kalunga.preco_ficha(unico), 28.5)
        self.assertEqual(kalunga.preco_ficha(sem_cabecalho), 1044.05)
        self.assertIsNone(kalunga.preco_ficha("<html></html>"))

    def test_vazio(self):
        self.assertEqual(kalunga.parse(""), [])
        self.assertEqual(kalunga.parse(None), [])


if __name__ == "__main__":
    unittest.main()
