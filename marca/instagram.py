"""Gera posts do Instagram (1080x1350) com os dados reais do site.

Uso: .venv/Scripts/python marca/instagram.py <dados.json> <pasta de saída>
O dados.json sai do site (P com Muquirômetro e Black Fraude já calculados).
"""
import html, json, pathlib, sys
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
DADOS, SAIDA = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
SAIDA.mkdir(parents=True, exist_ok=True)
D = json.loads(DADOS.read_text(encoding="utf-8"))
LOJA = {"kabum": "KaBuM!", "amazon": "Amazon", "samsung": "Samsung", "kalunga": "Kalunga", "motorola": "Motorola",
        "steam": "Steam", "playstation": "PlayStation Store"}
BRT = timezone(timedelta(hours=-3))


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pega(trecho, kind, cur=None):
    xs = [x for x in D if trecho in x["n"] and x["kind"] == kind and (cur is None or abs(x["cur"] - cur) < .01)]
    assert len(xs) == 1, (trecho, len(xs))
    return xs[0]


ICONE = ('<svg width="56" height="56" viewBox="-0.5 -3.5 25 25" fill="none" stroke-linecap="round" stroke-linejoin="round">'
         '<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z" stroke="#00e5ff" stroke-width="2"/>'
         '<path d="M8 8C5.6 6.4 3.4 4.2 2.2 1.8 1.2-.2 2.4-2.2 4.6-2.2 6.6-2.2 8-.8 8.4 1" stroke="#a6ff3b" stroke-width="1.6"/>'
         '<circle cx="8" cy="8" r="1.7" fill="#a6ff3b"/></svg>')

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1350px;background:#06080d;color:#e8eef9;font-family:'Segoe UI',system-ui,sans-serif;position:relative;overflow:hidden;
background-image:radial-gradient(900px 500px at 100% 0%,rgba(0,229,255,.14),transparent 60%),radial-gradient(800px 500px at 0% 100%,rgba(166,255,59,.10),transparent 60%),
linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);background-size:auto,auto,44px 44px,44px 44px}
.in{position:absolute;inset:70px 76px}
.top{display:flex;align-items:center;gap:14px;font-weight:800;font-size:34px;letter-spacing:-.5px}
.top b{color:#00e5ff}
.pg{margin-left:auto;font:700 22px ui-monospace,Consolas,monospace;color:#5d6a85}
.tag{display:inline-block;font:800 26px ui-monospace,Consolas,monospace;letter-spacing:1px;padding:10px 18px;border-radius:12px;border:2px solid var(--c);color:var(--c);background:color-mix(in srgb,var(--c) 10%,transparent)}
h1{font-size:104px;line-height:1;letter-spacing:-3px;font-weight:800}
h2{font-size:58px;line-height:1.08;letter-spacing:-1.5px;font-weight:800}
.mut{color:#8b98b2}
.foot{position:absolute;left:0;right:0;bottom:0;display:flex;justify-content:space-between;font:600 22px ui-monospace,Consolas,monospace;color:#5d6a85}
.card{background:#0d1320;border:2px solid #1c2538;border-radius:28px;padding:34px}
.img{height:350px;background:#fff;border-radius:22px;display:flex;align-items:center;justify-content:center;overflow:hidden}
.img img{max-height:310px;max-width:88%;object-fit:contain}
.preco{font-size:92px;font-weight:800;letter-spacing:-2px;line-height:1}
.row{display:flex;gap:18px}
.box{flex:1;background:#111a2b;border:1px solid #26314a;border-radius:18px;padding:18px 22px}
.box small{display:block;font:700 19px ui-monospace,Consolas,monospace;color:#8b98b2;letter-spacing:.5px;margin-bottom:6px}
.box b{font-size:38px;letter-spacing:-.5px}
.th{display:flex;height:16px;border-radius:999px;overflow:hidden}.th i{flex:1}
.cta{display:inline-block;background:linear-gradient(90deg,#a6ff3b,#5dffa0);color:#06080d;font-weight:800;font-size:40px;padding:22px 34px;border-radius:20px}
"""


def pagina(corpo, n, total):
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class='in'>"
            f"<div class='top'>{ICONE}<span>Muquirana<b>Tech</b></span><span class='pg'>{n}/{total}</span></div>"
            f"{corpo}</div></body></html>")


def grafico(p, cor):
    pts = [(datetime.fromisoformat(d).timestamp(), v) for d, v in p["pts"]]
    W, H, PAD = 868, 230, 14
    xs, ys = [t for t, _ in pts], [v for _, v in pts] + [p["normal"] or p["cur"]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys) * .95, max(ys) * 1.05
    X = lambda t: PAD + (t - x0) / max(1, x1 - x0) * (W - 2 * PAD)
    Y = lambda v: PAD + (1 - (v - y0) / (y1 - y0)) * (H - 2 * PAD)
    linha = " ".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in pts)
    yn = Y(p["normal"]) if p["normal"] else None
    norm = (f"<line x1='0' x2='{W}' y1='{yn:.1f}' y2='{yn:.1f}' stroke='#8b98b2' stroke-width='3' stroke-dasharray='10 10'/>"
            f"<rect x='0' y='{yn - 36:.1f}' width='190' height='30' rx='6' fill='#0d1320'/>"
            f"<text x='4' y='{yn - 12:.1f}' fill='#8b98b2' font-size='22' font-family='Consolas'>preço normal</text>") if yn else ""
    tx, ty = X(xs[-1]), Y(ys[len(pts) - 1])
    meses = "jan fev mar abr mai jun jul ago set out nov dez".split()
    d0 = datetime.fromisoformat(p["pts"][0][0])
    rot = (f"<text x='{PAD}' y='{H + 30}' fill='#5d6a85' font-size='22' font-family='Consolas'>{meses[d0.month - 1]}/{d0.year % 100}</text>"
           f"<text x='{W - PAD}' y='{H + 30}' text-anchor='end' fill='#5d6a85' font-size='22' font-family='Consolas'>hoje</text>")
    return (f"<svg width='{W}' height='{H + 40}' style='display:block'>{norm}{rot}"
            f"<polyline points='{linha}' fill='none' stroke='{cor}' stroke-width='6' stroke-linejoin='round' stroke-linecap='round'/>"
            f"<circle cx='{tx:.1f}' cy='{ty:.1f}' r='12' fill='{cor}'/></svg>")


def slide_produto(p, nome, tipo):
    if tipo == "firmeza":
        cor, selo = "#a6ff3b", "BLACK FIRMEZA"
        destaque = f"<span style='color:#a6ff3b'>{-p['vs'] * 100:.0f}% abaixo</span> do preço normal"
        caixas = [("HOJE", brl(p["cur"]), "#a6ff3b"), ("PREÇO NORMAL", brl(p["normal"]), "#e8eef9"),
                  ("MENOR JÁ VISTO", brl(p["min"]), "#e8eef9")]
    else:
        cor, selo = "#ffb020", "SEGURA A CARTEIRA"
        destaque = f"<span style='color:#ff4d6d'>{p['vs'] * 100:.0f}% acima</span> do preço normal"
        caixas = [("HOJE", brl(p["cur"]), "#ff4d6d"), ("PREÇO NORMAL", brl(p["normal"]), "#e8eef9"),
                  ("MENOR JÁ VISTO", brl(p["min"]), "#a6ff3b")]
    bx = "".join(f"<div class='box'><small>{a}</small><b style='color:{c}'>{v}</b></div>" for a, v, c in caixas)
    return (f"<div style='margin-top:44px' class='card'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:24px'>"
            f"<span class='tag' style='--c:{cor}'>{selo}</span><span class='mut' style='font-size:28px'>na {LOJA[p['st']]}</span></div>"
            f"<div class='img'><img src='{html.escape(p['img'])}'></div>"
            f"<h2 style='font-size:46px;margin-top:26px'>{html.escape(nome)}</h2>"
            f"<div style='font-size:34px;margin-top:10px;font-weight:700'>{destaque}</div>"
            f"<div class='row' style='margin-top:24px'>{bx}</div>"
            f"<div style='margin-top:24px'>{grafico(p, cor)}</div></div>")


def visto(p):
    return datetime.fromisoformat(p["at"]).astimezone(BRT).strftime("%d/%m às %Hh%M")


def rodape(txt="muquiranatech.com.br"):
    return f"<div class='foot'><span>{txt}</span><span>preço muda: confira na loja</span></div>"


def gera(nome_post, slides):
    pasta = SAIDA / nome_post
    pasta.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="msedge")
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, corpo in enumerate(slides, 1):
            pg.set_content(pagina(corpo, i, len(slides)), wait_until="networkidle")
            pg.screenshot(path=str(pasta / f"{i:02d}.png"))
        b.close()
    print("ok", pasta)


# ---------- Post 1: Black Firmeza ----------
FIRMEZA = [
    (pega("TCL 65 Polegadas QD-Mini", "firmeza"), "Smart TV TCL 65\" QD-Mini LED 4K C6K"),
    (pega("Ryzen 5 5600XT", "firmeza"), "Processador AMD Ryzen 5 5600XT"),
    (pega("HW-B400F", "firmeza"), "Soundbar Samsung HW-B400F"),
    (pega("JBL CLIP5", "firmeza"), "Caixa de som JBL Clip 5"),
    (pega("DualSense, PlayStation 5, Bluetooth, Branco", "firmeza"), "Controle DualSense PS5 (branco)"),
    (pega("Echo Dot 5", "firmeza", 349.9), "Echo Dot 5ª geração com Alexa"),
]
quando = visto(FIRMEZA[0][0])
capa1 = (f"<div style='margin-top:150px'><span class='tag' style='--c:#a6ff3b'>BLACK FIRMEZA</span>"
         f"<h1 style='margin-top:34px'>Desconto<br><span style='color:#a6ff3b'>de verdade</span><br>existe.</h1>"
         f"<p class='mut' style='font-size:42px;margin-top:40px;line-height:1.3'>{len(FIRMEZA)} produtos que estão <b style='color:#e8eef9'>abaixo do preço normal</b> "
         f"dos últimos meses. Conferido no histórico, não na etiqueta da loja.</p>"
         f"<p style='font-size:34px;margin-top:60px;color:#00e5ff;font-weight:700'>Arrasta pro lado →</p></div>{rodape('preços de ' + quando)}")
fim = (f"<div style='margin-top:150px'><h2 style='font-size:76px'>Antes de comprar,<br>pergunta pro <span style='color:#a6ff3b'>Muquirana</span>.</h2>"
       f"<p class='mut' style='font-size:40px;margin-top:36px;line-height:1.35'>Mais de 4.700 produtos com histórico de preço, "
       f"só em lojas e vendedores confiáveis.</p>"
       f"<div style='margin-top:60px'><span class='cta'>muquiranatech.com.br</span></div>"
       f"<p style='font-size:32px;margin-top:40px;color:#00e5ff;font-weight:700'>Link na bio · Salva este post 🔖</p>"
       f"<div class='th' style='margin-top:90px'><i style='background:#a6ff3b'></i><i style='background:#00e5ff'></i><i style='background:#ffb020'></i><i style='background:#ff4d6d'></i></div></div>"
       f"{rodape()}")
gera("01-black-firmeza", [capa1] + [slide_produto(p, n, "firmeza") + rodape("preço de " + visto(p)) for p, n in FIRMEZA] + [fim])

# ---------- Post 2: subiram antes da Black ----------
ALTA = [
    (pega("iPhone 17 Pro Apple 256GB", "fraude"), "iPhone 17 Pro 256GB"),
    (pega("RTX 5060 EAGLE MAX", "fraude"), "Placa de vídeo RTX 5060 Gigabyte Eagle"),
    (pega("Fire TV Stick HD 2ª Geração", "fraude"), "Fire TV Stick HD (2ª geração)"),
]
capa2 = (f"<div style='margin-top:150px'><span class='tag' style='--c:#ffb020'>SEGURA A CARTEIRA</span>"
         f"<h1 style='margin-top:34px'>Subiu<br><span style='color:#ff4d6d'>antes</span> da<br>Black.</h1>"
         f"<p class='mut' style='font-size:42px;margin-top:40px;line-height:1.3'>Estes produtos estão <b style='color:#e8eef9'>mais caros que o preço normal</b> "
         f"dos últimos meses. Se puder, espere.</p>"
         f"<p style='font-size:34px;margin-top:60px;color:#00e5ff;font-weight:700'>Arrasta pro lado →</p></div>{rodape('preços de ' + visto(ALTA[0][0]))}")
gera("02-segura-a-carteira", [capa2] + [slide_produto(p, n, "alta") + rodape("preço de " + visto(p)) for p, n in ALTA] + [fim])

# ---------- Post 3: como saber se a promoção é de verdade ----------
T = [("#a6ff3b", "ATÉ O MUQUIRANA COMPRA", "no máximo 2% acima do menor preço já visto"),
     ("#00e5ff", "MUQUIRANA APROVA", "até 10% acima do menor preço"),
     ("#ffb020", "SEGURA A CARTEIRA", "até 30% acima do menor preço"),
     ("#ff4d6d", "CILADA!", "mais de 30% acima do menor preço")]
e1 = ("<div style='margin-top:150px'><span class='tag' style='--c:#00e5ff'>GUIA RÁPIDO</span>"
      "<h1 style='margin-top:34px;font-size:96px'>A promoção é <span style='color:#a6ff3b'>de verdade</span> ou <span style='color:#ff4d6d'>cilada</span>?</h1>"
      "<p class='mut' style='font-size:42px;margin-top:40px;line-height:1.3'>3 passos para não cair em desconto falso.</p>"
      f"<p style='font-size:34px;margin-top:60px;color:#00e5ff;font-weight:700'>Arrasta pro lado →</p></div>{rodape()}")
e2 = ("<div style='margin-top:110px'><span class='tag' style='--c:#ff4d6d'>PASSO 1</span>"
      "<h2 style='margin-top:30px;font-size:72px'>Ignore o “de R$ 999 por R$ 499”.</h2>"
      "<p class='mut' style='font-size:40px;margin-top:34px;line-height:1.4'>O preço “de” é a loja que escolhe. Às vezes o produto <b style='color:#e8eef9'>nunca</b> "
      "foi vendido por aquele valor. Um “-50%” sobre um preço inventado não é desconto.</p>"
      "<div class='card' style='margin-top:44px;font-size:38px'><s style='color:#5d6a85'>de R$ 999,00</s><br>"
      "<b style='font-size:70px'>R$ 499,00</b> <span class='tag' style='--c:#ff4d6d;font-size:24px;vertical-align:middle'>-50%?</span>"
      f"<p class='mut' style='font-size:30px;margin-top:14px'>Se ele custou R$ 499 o ano todo, o desconto é zero.</p></div></div>{rodape()}")
faixas = "".join(f"<div class='card' style='border-left:10px solid {c};padding:24px 30px;margin-top:18px'>"
                 f"<div style='font:800 30px Consolas,monospace;color:{c}'>{k}</div><div class='mut' style='font-size:32px;margin-top:4px'>{t}</div></div>" for c, k, t in T)
e3 = ("<div style='margin-top:90px'><span class='tag' style='--c:#00e5ff'>PASSO 2</span>"
      "<h2 style='margin-top:30px'>Compare com o <span style='color:#a6ff3b'>menor preço</span> que ele já teve.</h2>"
      f"{faixas}<p class='mut' style='font-size:30px;margin-top:24px'>É assim que o Muquirômetro dá o veredito.</p></div>{rodape()}")
e4 = ("<div style='margin-top:110px'><span class='tag' style='--c:#ffb020'>PASSO 3</span>"
      "<h2 style='margin-top:30px;font-size:68px'>Desconfie do preço que <span style='color:#ff4d6d'>subiu</span> no último mês.</h2>"
      "<p class='mut' style='font-size:40px;margin-top:34px;line-height:1.4'>Subir o preço semanas antes para “baixar” na Black Friday é o truque mais velho do varejo. "
      "Compare com o preço <b style='color:#e8eef9'>de 1 a 3 meses atrás</b>.</p>"
      "<div class='row' style='margin-top:44px'>"
      "<div class='card' style='flex:1;border-top:6px solid #ff4d6d'><div style='font:800 30px Consolas,monospace;color:#ff4d6d'>BLACK FRAUDE</div>"
      "<p class='mut' style='font-size:30px;margin-top:10px'>Subiu antes e “baixou” para o preço de sempre.</p></div>"
      "<div class='card' style='flex:1;border-top:6px solid #a6ff3b'><div style='font:800 30px Consolas,monospace;color:#a6ff3b'>BLACK FIRMEZA</div>"
      f"<p class='mut' style='font-size:30px;margin-top:10px'>8% ou mais abaixo do preço normal. Desconto de verdade.</p></div></div></div>{rodape()}")
gera("03-guia-promocao", [e1, e2, e3, e4, fim])
