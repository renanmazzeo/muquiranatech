import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "collector"))
import parcelas  # noqa: E402


class TestParcelas(unittest.TestCase):
    def test_kabum_sem_e_com_juros(self):
        self.assertEqual(parcelas.de_texto("10x de R$ 117,64", 1176.46), {"n": 10, "v": 117.64, "total": 1176.4, "juros": False})
        self.assertTrue(parcelas.de_texto("12x de R$ 110,00", 1176.46)["juros"])
        self.assertIsNone(parcelas.de_texto("", 100))
        self.assertIsNone(parcelas.de_texto("10x de R$ 10,00", None))  # sem referência, não afirma nada

    def test_vtex(self):
        ins = [{"PaymentSystemName": "Visa", "NumberOfInstallments": n, "Value": round(2443 / n, 2), "InterestRate": 0,
                "TotalValuePlusInterestRate": 2443} for n in (1, 10, 18)]
        ins += [{"PaymentSystemName": "Visa", "NumberOfInstallments": 21, "Value": 130, "InterestRate": 1.99,
                 "TotalValuePlusInterestRate": 2730}, {"PaymentSystemName": "Pix", "NumberOfInstallments": 1, "Value": 2198.7}]
        self.assertEqual(parcelas.vtex(ins), {"n": 18, "v": 135.72, "total": 2443.0, "juros": False})


if __name__ == "__main__":
    unittest.main()
