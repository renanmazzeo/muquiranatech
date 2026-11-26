"""Testes do leitor da Steam (resposta de exemplo no formato da API storesearch)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collector"))
import kabum  # noqa: E402
import steam  # noqa: E402

RESP = {"total": 5, "items": [
    {"type": "app", "name": "ELDEN RING", "id": 1245620, "price": {"currency": "BRL", "initial": 22990, "final": 15993}},
    {"type": "app", "name": "Jogo Grátis", "id": 5},
    {"type": "app", "name": "Jogo em dólar", "id": 6, "price": {"currency": "USD", "initial": 1000, "final": 1000}},
    {"type": "app", "name": "ELDEN RING Soundtrack", "id": 7, "price": {"currency": "BRL", "initial": 3000, "final": 3000}},
    {"type": "bundle", "name": "Pacote", "id": 8, "price": {"currency": "BRL", "initial": 100, "final": 100}},
]}


class Steam(unittest.TestCase):
    def test_parse(self):
        itens = steam.parse(RESP)
        self.assertEqual([i["code"] for i in itens], ["1245620", "7"])  # sem preço, em dólar e pacote: fora
        e = itens[0]
        self.assertEqual((e["price"], e["list_price"], e["seller"]), (159.93, 229.9, "Steam"))
        self.assertEqual(e["url"], "https://store.steampowered.com/app/1245620/")

    def test_pick_tira_trilha_sonora(self):
        escolhidos = kabum.pick(steam.parse(RESP), ["elden ring"], 1, ["Steam"], ["soundtrack"])
        self.assertEqual([i["code"] for i in escolhidos], ["1245620"])

    def test_resposta_vazia(self):
        self.assertEqual(steam.parse({}), [])
        self.assertEqual(steam.parse(None), [])


if __name__ == "__main__":
    unittest.main()
