"""Testes do leitor do Mercado Livre (resposta de exemplo da API de busca)."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collector"))
import kabum  # noqa: E402
import mercadolivre as ml  # noqa: E402

RESP = {"results": [
    {"id": "MLB1", "title": "Monitor Gamer LG 27", "price": 999.9, "original_price": 1299.0, "condition": "new",
     "official_store_id": 77, "available_quantity": 5, "permalink": "https://produto.mercadolivre.com.br/MLB-1",
     "thumbnail": "http://http2.mlstatic.com/D_1-I.jpg"},
    {"id": "MLB2", "title": "Monitor de vendedor comum", "price": 500, "condition": "new",
     "official_store_id": None, "available_quantity": 1},
    {"id": "MLB3", "title": "Monitor usado", "price": 400, "condition": "used", "official_store_id": 77},
    {"id": "MLB4", "title": "Monitor esgotado", "price": 800, "condition": "new", "official_store_id": 5,
     "available_quantity": 0},
]}


class MercadoLivre(unittest.TestCase):
    def test_so_loja_oficial_e_novo(self):
        itens = ml.parse(RESP)
        self.assertEqual([i["code"] for i in itens], ["MLB1", "MLB4"])
        i = itens[0]
        self.assertEqual((i["price"], i["list_price"], i["seller"]), (999.9, 1299.0, "Loja oficial"))
        self.assertTrue(i["img"].startswith("https://") and i["img"].endswith("-O.jpg"))

    def test_pick_tira_esgotado(self):
        ok = kabum.pick(ml.parse(RESP), ["monitor"], 5, ["Loja oficial"], [])
        self.assertEqual([i["code"] for i in ok], ["MLB1"])

    def test_sem_credenciais_pula(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(ml.configurado())
        with mock.patch.dict(os.environ, {"ML_CLIENT_ID": "a", "ML_CLIENT_SECRET": "b"}):
            self.assertTrue(ml.configurado())

    def test_token_e_busca(self):
        def fake_post(url, **kw):
            self.assertEqual(kw["data"]["grant_type"], "client_credentials")
            return mock.Mock(status_code=200, json=lambda: {"access_token": "T", "expires_in": 21600},
                             raise_for_status=lambda: None)

        def fake_get(url, **kw):
            self.assertEqual(kw["headers"]["Authorization"], "Bearer T")
            self.assertEqual(kw["params"]["official_store"], "all")
            return mock.Mock(status_code=200, json=lambda: RESP, raise_for_status=lambda: None)

        ml._token.update(v=None, ate=0)
        with mock.patch.dict(os.environ, {"ML_CLIENT_ID": "a", "ML_CLIENT_SECRET": "b"}), \
                mock.patch("requests.post", fake_post), mock.patch("requests.get", fake_get):
            self.assertEqual(len(ml.search("monitor-gamer")), 2)

    def test_token_recusado(self):
        ml._token.update(v=None, ate=0)
        with mock.patch.dict(os.environ, {"ML_CLIENT_ID": "a", "ML_CLIENT_SECRET": "b"}), \
                mock.patch("requests.post", lambda *a, **k: mock.Mock(status_code=401)):
            with self.assertRaises(ml.Blocked):
                ml.search("x")


if __name__ == "__main__":
    unittest.main()
