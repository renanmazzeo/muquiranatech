import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collector"))
import samsung  # noqa: E402


def sku(price, lista, qtd=10, pix=None, seller="1"):
    inst = [{"PaymentSystemName": "Visa", "NumberOfInstallments": 1, "Value": price}]
    if pix:
        inst.append({"PaymentSystemName": "Pix", "NumberOfInstallments": 1, "Value": pix})
    return {"images": [{"imageUrl": "https://img/x.jpg"}],
            "sellers": [{"sellerId": seller, "commertialOffer": {
                "Price": price, "ListPrice": lista, "AvailableQuantity": qtd, "Installments": inst}}]}


class TestSamsung(unittest.TestCase):
    def test_preco_do_pix_e_sku_mais_barato_disponivel(self):
        p = {"productId": "6752", "productName": "Celular Samsung Galaxy S25 5G, 256GB", "link": "https://x/p",
             "items": [sku(3888, 7299, pix=3499.2), sku(3000, 7299, qtd=0), sku(3999, 7299, pix=3599.1)]}
        it = samsung.parse([p])[0]
        self.assertEqual((it["price"], it["list_price"], it["seller"]), (3499.2, 7299, "Samsung"))

    def test_outro_vendedor_ou_esgotado_fica_fora(self):
        self.assertEqual(samsung.parse([{"productId": "1", "productName": "X", "items": [sku(100, 100, seller="2")]}]), [])
        self.assertEqual(samsung.parse([{"productId": "2", "productName": "Y", "items": [sku(100, 100, qtd=0)]}]), [])


if __name__ == "__main__":
    unittest.main()
