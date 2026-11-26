"""Categoria do site a partir do nome do produto.

Usado na coleta por catálogo (a categoria inteira da loja), onde não há uma busca dizendo a categoria.
As lojas escrevem o tipo no começo do nome ("Placa de Vídeo ...", "Processador ...", "Jogo ... PS5"),
então a regra olha primeiro o começo do nome; só depois procura marcas inconfundíveis no meio.
As categorias seguem as mesmas da watchlist (ex.: headset fica em "perif", impressora em "casa").
"""
import re

from kabum import norm

# (categoria, expressão no COMEÇO do nome já normalizado: minúsculas, sem acento, hífen vira espaço)
INICIO = [
    ("game", r"jogo |game |gift card|cartao presente|assinatura|playstation plus|xbox game pass"),
    ("console", r"console |controle|joy con|dualsense|dualshock"),
    ("notebook", r"notebook|macbook|chromebook|ultrabook|pc gamer|computador|imac|mini pc|all in one"),
    ("monitor", r"monitor"),
    ("gpu", r"placa de video"),
    ("cpu", r"processador"),
    ("mobo", r"placa mae"),
    ("ram", r"memoria"),
    ("ssd", r"ssd|hd |hd externo|cartao (de )?memoria|cartao micro|micro ?sd|pen ?drive|disco |nas |case para (hd|ssd)"),
    ("fonte", r"fonte"),
    ("gab", r"gabinete|water ?cooler|cooler|air cooler|fan |ventoinha|kit fan|pasta termica"),
    ("celular", r"smartphone|iphone|celular|carregador|power ?bank|bateria portatil|cabo (usb|tipo|lightning)"),
    ("tablet", r"tablet|ipad|kindle|e ?reader|leitor de livros"),
    ("wear", r"smartwatch|relogio|smartband|apple watch|galaxy watch|pulseira inteligente"),
    ("tv", r"smart tv|tv |televis|projetor|streaming|fire tv|chromecast|tv box"),
    ("rede", r"roteador|repetidor|switch|adaptador (wi|de rede|usb wi|bluetooth)|antena|kit starlink|starlink|"
             r"access point|nobreak|estabilizador|filtro de linha|modem|sistema mesh|placa de rede|cabo de rede"),
    ("casa", r"echo|lampada|tomada inteligente|fechadura|camera (de seguranca|ip|inteligente|wi)|campainha|"
             r"hub (zigbee|gateway)|sensor|interruptor|robo aspirador|aspirador robo|impressora|multifuncional"),
    ("audio", r"fone|earbuds|airpods|galaxy buds|caixa de som|soundbar|home theater|amplificador|receiver|"
              r"toca discos|vitrola|alto falante"),
    ("perif", r"mouse|teclado|headset|webcam|mousepad|microfone|cadeira|mesa|volante|scanner|hub usb|"
              r"suporte|mochila|kit gamer|mesa digitalizadora|stream deck|placa de captura"),
]
# marcas/produtos inconfundíveis no meio do nome (ex.: "Apple iPad 11", "Amazon Echo Dot")
MEIO = [
    ("tablet", r"\bipad\b|\bkindle\b|\bgalaxy tab\b"),
    ("celular", r"\biphone\b|\bgalaxy [asz]\d|\bmoto g\d|\bredmi\b"),
    ("notebook", r"\bmacbook\b"),
    ("wear", r"\bapple watch\b|\bgalaxy watch\b|\bsmartwatch\b"),
    ("audio", r"\bairpods\b|\bgalaxy buds\b|\bfone\b"),
    ("casa", r"\becho (dot|show|pop)\b|\balexa\b"),
    ("console", r"\bplaystation 5\b|\bps5\b|\bxbox series\b|\bnintendo switch\b"),
]
_INICIO = [(c, re.compile(r"^(?:%s)" % e)) for c, e in INICIO]
_MEIO = [(c, re.compile(e)) for c, e in MEIO]


def classificar(nome, padrao="perif"):
    n = norm(nome).strip()
    for cat, rx in _INICIO:
        if rx.match(n):
            return cat
    for cat, rx in _MEIO:
        if rx.search(n):
            return cat
    return padrao
