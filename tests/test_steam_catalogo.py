import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "collector"))
import steam  # noqa: E402

HTML = ('<a href="https://store.steampowered.com/app/381210/Dead_by_Daylight/?snr=1" data-ds-appid="381210" '
        'data-ds-itemkey="App_381210" class="search_result_row"><span class="title">Dead by Daylight</span>'
        '<div data-price-final="5388">R$53,88</div></a>'
        '<a href="https://store.steampowered.com/app/9/X/" data-ds-itemkey="Sub_9"><span class="title">Pacote</span></a>')


class TestSteamCatalogo(unittest.TestCase):
    def test_lista_so_jogos(self):
        self.assertEqual(steam.lista(HTML), [("381210", "Dead by Daylight")])


if __name__ == "__main__":
    unittest.main()
