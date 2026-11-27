import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "collector"))
import xiaomi  # noqa: E402


def prod(nome="REDMI Note 17 5G 256GB", folha="Smartphones", disp="I", venda=3999.99, lista=3999.99,
         vista=3679.99, desconto=8.0):
    bi = {"Installments": 1, "InstallmentPrice": vista, "Discount": desconto} if vista else None
    return {"ProductID": 353174, "Name": nome, "LeafCategoryName": folha, "Availability": disp,
            "Url": "/smartphone-redmi-note-17-p353174", "MediaSmall": "/Custom/Content/Products/a.webp",
            "Price": {"SalesPrice": venda, "ListPrice": lista, "BestInstallment": bi,
                      "MaxInstallmentsNoInterest": {"Installments": 12, "InstallmentPrice": 333.33,
                                                    "RetailPrice": venda}}}


def pagina(*ps):
    return {"Model": {"Grid": {"PageCount": 34, "Products": list(ps)}}}


class TestXiaomi(unittest.TestCase):
    def test_preco_a_vista_da_ficha(self):
        itens, total = xiaomi.parse(pagina(prod()))
        it = itens[0]
        self.assertEqual(total, 34)
        self.assertEqual((it["price"], it["list_price"], it["seller"], it["cat"]),
                         (3679.99, 3999.99, "Xiaomi", "celular"))
        self.assertEqual(it["parc"], {"n": 12, "v": 333.33, "total": 3999.99, "juros": False})
        self.assertEqual(it["url"], "https://www.mibrasil.com.br/smartphone-redmi-note-17-p353174")

    def test_sem_desconto_a_vista_usa_preco_de_venda(self):
        it = xiaomi.parse(pagina(prod(vista=None)))[0][0]
        self.assertEqual(it["price"], 3999.99)

    def test_fora_de_estoque_e_categorias_fora(self):
        self.assertEqual(xiaomi.parse(pagina(prod(disp="O")))[0], [])
        self.assertEqual(xiaomi.parse(pagina(prod(nome="Capa Kapps", folha="Capas")))[0], [])
        self.assertEqual(xiaomi.parse(pagina(prod(nome="Kit 2 Panos para Robô", folha="Utilidades Domésticas")))[0], [])

    def test_categoria_pelo_nome(self):
        robo = xiaomi.parse(pagina(prod(nome="Robô Aspirador S40", folha="Utilidades Domésticas")))[0][0]
        mouse = xiaomi.parse(pagina(prod(nome="Mouse Sem Fio Lite", folha="Roteadores e Periféricos")))[0][0]
        rot = xiaomi.parse(pagina(prod(nome="Roteador Wi-fi Mi Router 4C", folha="Roteadores e Periféricos")))[0][0]
        self.assertEqual((robo["cat"], mouse["cat"], rot["cat"]), ("casa", "perif", "rede"))


if __name__ == "__main__":
    unittest.main()
