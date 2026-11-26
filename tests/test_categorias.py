import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collector"))
from categorias import classificar  # noqa: E402


class TestCategorias(unittest.TestCase):
    def test_tipo_no_comeco_do_nome(self):
        casos = {
            "Placa de Vídeo MSI RTX 5070 Ti Ventus 3X OC, 16GB": "gpu",
            "Processador AMD Ryzen 5 8500G + Placa Mãe ASUS TUF GAMING A620": "cpu",  # kit: vale o 1º item
            "Placa-Mãe MSI B760M Gaming Plus, Intel LGA 1700": "mobo",
            "Memória RAM Kingston Fury Beast, 8GB, 3200MHz, DDR4": "ram",
            "Notebook Lenovo IdeaPad Slim 3, i7-13620H, 8GB DDR5, 512GB SSD": "notebook",  # não é "ssd"
            "Jogo Borderlands 4, PS5 - TT000265PS5": "game",
            "Controle Sem Fio PlayStation 5 Sony DualSense": "console",
            "Headset Gamer Razer Kaira X, Para Xbox e PC": "perif",
            "Fone de Ouvido JBL Wave Buds 2": "audio",
            "Water Cooler MSI MAG Coreliquid A13, ARGB, 360mm": "gab",
            "Monitor Gamer Samsung Odyssey G40, 27\" FHD, 240Hz": "monitor",
            "Smart TV 43\" Samsung Full HD": "tv",
            "Roteador TP-Link Deco M5, Gigabit": "rede",
            "Echo Dot 5ª geração Amazon, com Alexa": "casa",
            "Kindle Paperwhite Amazon 7\", 16GB": "tablet",
            "Apple Watch SE 3 GPS, Caixa estelar de Alumínio de 40 mm": "wear",
            "Pen Drive 128GB SanDisk Ultra Shift, USB 3.2": "ssd",
            "PC Gamer Mancer, Intel Core i5, 16GB": "notebook",
        }
        for nome, cat in casos.items():
            self.assertEqual(classificar(nome), cat, nome)

    def test_meio_do_nome_e_padrao(self):
        self.assertEqual(classificar("Apple iPad 11 A16, Wi-Fi, 128GB"), "tablet")
        self.assertEqual(classificar("Coisa Desconhecida XPTO", "audio"), "audio")


if __name__ == "__main__":
    unittest.main()
