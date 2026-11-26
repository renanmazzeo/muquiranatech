"""Testes do leitor da PlayStation Store (página de busca de exemplo, montada à mão no formato real)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collector"))
import playstation  # noqa: E402

PAGINA = (Path(__file__).parent / "fixtures" / "playstation_busca.html").read_text(encoding="utf-8")


class PlayStation(unittest.TestCase):
    def test_parse(self):
        itens = playstation.parse(PAGINA)
        # preço só de assinante fora; repetido (mesmo id) só uma vez
        self.assertEqual([i["code"] for i in itens], ["UP1-A", "UP1-B"])
        n, p = itens[0], itens[1]
        self.assertEqual((n["price"], n["list_price"], n["seller"]), (199.9, 199.9, "PlayStation Store"))
        self.assertEqual((p["price"], p["list_price"]), (149.95, 299.9))
        self.assertEqual(p["url"], "https://store.playstation.com/pt-br/product/UP1-B")
        self.assertTrue(p["img"].startswith("https://image.api.playstation.com/"))

    def test_reais(self):
        self.assertEqual(playstation._reais("R$1.234,56"), 1234.56)
        self.assertIsNone(playstation._reais("Grátis"))


if __name__ == "__main__":
    unittest.main()
