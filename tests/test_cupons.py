import datetime as dt
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "collector"))
import cupons  # noqa: E402


class TestCupons(unittest.TestCase):
    def test_vencido_some_e_manual_ganha(self):
        with tempfile.TemporaryDirectory() as d:
            man, auto = pathlib.Path(d, "m.json"), pathlib.Path(d, "a.json")
            man.write_text(json.dumps([{"loja": "lenovo", "codigo": "MUQUI10", "titulo": "10%", "pct": 10, "fonte": "manual"},
                                       {"loja": "lenovo", "codigo": "VELHO", "titulo": "x", "ate": "2026-01-01T00:00:00Z"}]),
                           encoding="utf-8")
            auto.write_text(json.dumps([{"loja": "lenovo", "codigo": "muqui10", "titulo": "repetido", "fonte": "lomadee"},
                                        {"loja": "lenovo", "codigo": "SEMTITULO"}]), encoding="utf-8")
            cupons.MANUAL, cupons.AUTO = man, auto
            v = cupons.validos(dt.datetime(2026, 11, 26, tzinfo=dt.timezone.utc))
        self.assertEqual([(c["codigo"], c["titulo"]) for c in v], [("MUQUI10", "10%")])


if __name__ == "__main__":
    unittest.main()
