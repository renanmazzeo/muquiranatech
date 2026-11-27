import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "collector"))
import concordia  # noqa: E402
import pcyes  # noqa: E402


def pagina_pcyes(*itens):
    d = {"props": {"pageProps": {"products": {"items": list(itens)}}}}
    return '<script id="__NEXT_DATA__" type="application/json">' + json.dumps(d) + "</script>"


def prod(sku="404940", final=3299, regular=4399, estoque="IN_STOCK"):
    return {"sku": sku, "url_key": "computador-x", "name": "Computador  PCYES ONE", "stock_status": estoque,
            "price_range": {"minimum_price": {"final_price": {"value": final}, "regular_price": {"value": regular}}},
            "cdn_images": json.dumps(["https://cdn.oderco.com.br/produtos/404940/a"])}


BLOCO = ('<div data-product-container-id="15565" data-ga4-name="Monitor Conc&oacute;rdia CZ238F">'
         '<a class="product__link" href="https://www.concordia.inf.br/monitor-cz238f">x</a>'
         '<img data-original="https://images.tcdn.com.br/img/a.jpg"><div class="product__offer">'
         '<span>De:</span> R$ <span>770,00</span> Por: R$ 589,00 R$ <b>530</b> , 10 à vista com desconto</div></div>')


class TestPcyes(unittest.TestCase):
    def test_preco_e_estoque(self):
        it = pcyes.parse(pagina_pcyes(prod()))[0]
        self.assertEqual((it["price"], it["list_price"], it["seller"]), (3299.0, 4399.0, "PCYes"))
        self.assertEqual(it["url"], "https://www.pcyes.com.br/computador-x")
        self.assertEqual(it["name"], "Computador PCYES ONE")
        self.assertEqual(pcyes.parse(pagina_pcyes(prod(estoque="OUT_OF_STOCK"))), [])


class TestConcordia(unittest.TestCase):
    def test_preco_a_vista(self):
        it = concordia.parse(BLOCO)[0]
        self.assertEqual((it["code"], it["price"], it["list_price"]), ("15565", 530.1, 770.0))
        self.assertEqual(it["name"], "Monitor Concórdia CZ238F")

    def test_esgotado_fora(self):
        self.assertEqual(concordia.parse(BLOCO.replace("à vista com desconto", "Esgotado!")), [])


if __name__ == "__main__":
    unittest.main()
