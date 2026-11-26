import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "collector"))
import lenovo  # noqa: E402


def prod(code="83V8S00000", final="2635.99", web="3806.69", status="Available", inv=1, compra=True,
         summary="IdeaPad Slim 3 AMD Ryzen 3 7320U 8GB 256GB SSD Linux 15.6\" FHD"):
    return {"id": code + "_x", "productCode": code, "productName": "IPS3 15AMN8", "summary": summary,
            "finalPrice": final, "webPrice": web, "marketingStatus": status, "inventoryStatus": inv,
            "purchaseFlag": compra, "url": "/p/laptops/ideapad/x/" + code.lower(),
            "media": {"thumbnail": {"imageAddress": "//p1-ofp.static.pub/medias/x.png"}}}


def resp(*ps):
    return {"data": {"pageCount": 1, "data": [{"products": list(ps)}]}}


class TestLenovo(unittest.TestCase):
    def test_preco_pix_e_nome(self):
        it = lenovo.parse(resp(prod()))[0]
        self.assertEqual(it["price"], 2635.99)        # finalPrice = "À vista no PIX"
        self.assertEqual(it["list_price"], 3806.69)   # webPrice = "De:"
        self.assertEqual(it["seller"], "Lenovo")
        self.assertTrue(it["name"].startswith("Lenovo IdeaPad Slim 3"))
        self.assertEqual(it["url"], "https://www.lenovo.com/br/pt/p/laptops/ideapad/x/83v8s00000")
        self.assertEqual(it["img"], "https://p1-ofp.static.pub/medias/x.png")

    def test_indisponivel_fica_fora(self):
        self.assertEqual(lenovo.parse(resp(prod(status="Coming Soon"), prod(inv=0), prod(compra=False),
                                           prod(final="0"))), [])

    def test_preco_da_ficha(self):
        j = {"data": {"83NS000LBR": [0, "ok", "83NS000LBR", "BRL", "3782.49", -1, -1, 0, [], "1417.5", 27.0, 2, -1,
                                     [3, "487450718175237", "0", "5199.99", 0]],
                      "X1": [1, "erro", "X1", "BRL", "0"]}}
        self.assertEqual(lenovo.ler_precos(j), {"83NS000LBR": (3782.49, 5199.99)})


if __name__ == "__main__":
    unittest.main()
