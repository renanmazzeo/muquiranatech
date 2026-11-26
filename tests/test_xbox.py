"""Testes do leitor da Xbox Store (página de busca de exemplo, montada à mão no formato real)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collector"))
import xbox  # noqa: E402

PAGINA = (Path(__file__).parent / "fixtures" / "xbox_busca.html").read_text(encoding="utf-8")


class Xbox(unittest.TestCase):
    def test_parse(self):
        itens = xbox.parse(PAGINA)
        # sem preço fora; repetido (mesmo id) só uma vez
        self.assertEqual([i["code"] for i in itens], ["9AAA", "9BBB"])
        n, p = itens
        self.assertEqual((n["price"], n["list_price"], n["seller"]), (199.0, 199.0, "Xbox Store"))
        self.assertEqual((p["name"], p["price"], p["list_price"]), ("Jogo em Promoção", 149.5, 299.0))
        self.assertTrue(p["url"].startswith("https://www.xbox.com/pt-BR/games/store/"))
        self.assertTrue(p["img"].startswith("https://store-images.s-microsoft.com/"))

    def test_pagina_real_guardada(self):
        real = Path(__file__).parent.parent / "docs" / "sondagens" / "html" / "xbox-html.html"
        if real.exists():
            self.assertGreaterEqual(len(xbox.parse(real.read_text(encoding="utf-8", errors="ignore"))), 5)


if __name__ == "__main__":
    unittest.main()
