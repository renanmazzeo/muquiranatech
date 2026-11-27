# MuquiranaTech: contexto do projeto

Portal de ofertas de tecnologia que compara o preço de hoje com o histórico, só com lojas e vendedores confiáveis.
Público: leigo em tecnologia. Todo o texto do site e dos commits é em português do Brasil.

> **Agente autônomo (tarefa agendada)?** Leia também [TAREFAS.md](TAREFAS.md) (o que fazer e as regras)
> e [DIARIO.md](DIARIO.md) (o que já foi feito). Registre no DIARIO.md tudo o que fizer.

## Regras do dono
- **Só serviços gratuitos.** Hospedagem, banco de dados e automação precisam ter plano grátis que aguente o uso.
- Mudanças grandes no site: testar antes. Todo push na `main` vai ao ar na hora (Cloudflare Pages e GitHub Pages).
- O site precisa transmitir credibilidade: preço igual ao da loja, hora da coleta, só vendedores confiáveis.
- O dono não é desenvolvedor: explicar em linguagem simples.

## Arquitetura
```
GitHub Actions (a cada 3h) ──► coleta KaBuM! ─┐
PC do dono (a cada 6h)        ► coleta Amazon ─┼─► mescla em data/muquirana.db ─► exporta data.js ─► push na main
                                               │                                                    │
Wayback Machine (domingo) ─► histórico KaBuM! ─┘              Cloudflare Pages / GitHub Pages ◄─────┘
```
- `index.html`: o site inteiro (HTML, CSS e JS num arquivo só). Lê `data.js`; sem ele, mostra dados fictícios.
  Busca inteligente (`rank()`): sem acento, "rtx3060" = "rtx 3060", aceita 1 letra errada ou trocada (2 em palavras
  longas), sinônimos (`SIN`: celular/smartphone, fone/headset...); número tem que bater exato. Painel de resultados
  embaixo da busca; a grade mostra 60 produtos por vez ("Ver mais").
- Outras páginas: `como-funciona.html` (explica Muquirômetro e Black Fraude: **se mudar os números no código, mude
  aqui também**), `privacidade.html` (LGPD e aviso de afiliado), `og.png` (prévia no WhatsApp, 1200×630) e `favicon.svg`.
- "O mesmo produto em outras lojas" (`codigos()`/`tracos()` em `index.html`): junta só com o mesmo código de modelo,
  mesma categoria e sem conflito de DDR, capacidade, número de modelo ou polegadas. Conservador de propósito.
- `LICENSE`: todos os direitos reservados (repositório público só para os robôs rodarem de graça).
- `collector/muq.py`: comandos
  - `coletar [--lojas kabum,amazon]`: preço de hoje. Cada loja usa a `pausa` definida para ela na watchlist.
  - `historico --meses N` (padrão 12, nunca mais de 1 ano), `--max-minutos`: Wayback, só KaBuM!. Baixa primeiro
    as cópias mais recentes e pula as que já baixou (tabela `wayback_done`).
  - `mesclar <copia.db> --lojas X [--wayback]`: junta no banco real só as linhas da loja X vindas de uma cópia.
  - `exportar`: gera `data.js` (sempre com fim de linha LF).
  - `MUQ_DB=<arquivo>`: faz qualquer comando usar outro banco. Os robôs coletam numa cópia e só no fim fazem
    `git fetch` + `reset` + `mesclar` + `exportar` + push. Assim um robô nunca apaga a coleta do outro.
- `collector/kabum.py`: lê o `__NEXT_DATA__` das buscas e categorias da KaBuM!. **Catálogo:** `catalogo(path)` lê a categoria
  inteira só com o filtro "Vendido pela KaBuM!" (`facet_filters`), 100 por página, sem `sort` (o robots.txt proíbe);
  as categorias ficam em `lojas.kabum.catalogo` na watchlist (~4.000 produtos). A categoria do site vem do nome do
  produto (`collector/categorias.py`); a de uma busca, quando existe, não é trocada. **Ofertas:** em promoções o preço real fica em
  `offer` (`priceWithDiscount`, `startsAt`/`endsAt`). `_item()` usa a oferta ativa no instante da página (agora, ou a
  data da cópia na Wayback). Ignorar a oferta foi o bug de 25/11/2026, quando o site mostrava preços mais altos que
  os da loja. O preço "Prime" (só para assinantes) não é usado. `pick()` (usado por todas as lojas) filtra por
  vendedor confiável, disponibilidade, palavras obrigatórias (`must`) e proibidas (`not`).
- `collector/amazon.py`: busca com filtro `rh=p_6:A1ZZFT5FULY4LN` (só "vendido e entregue pela Amazon.com.br");
  ignora anúncios patrocinados. **A Amazon bloqueia IPs do GitHub (503)**, por isso ela é coletada pelo PC do
  dono. Se pedirem muitas buscas seguidas, o PC também é bloqueado por algumas horas: nunca rode testes em massa.
- `collector/coletar-pc.ps1`: o robô do PC. Fica numa cópia própria do repositório em
  `%LOCALAPPDATA%\MuquiranaTech\repo`, com log em `%LOCALAPPDATA%\MuquiranaTech\coleta.log`. Tarefa do Windows:
  "MuquiranaTech - Amazon". Para reinstalar: `-Instalar`.
- `collector/watchlist.json`: `lojas` (nome, vendedores confiáveis, `not`, `pausa` e `max_busca` por loja; `catalogo` na KaBuM!) e 124 `buscas`
  comuns (`q`, `cat`, `must`, `not`, `max`), com ajustes por loja (ex.: `"amazon": {"must": [...]}` ou
  `{"skip": true}`). Antes de adicionar uma busca, teste o `search` + `pick` e confira se o produto bate com o nome.
- `data/muquirana.db`: SQLite. `products` (inclui `offer_ends` e `checked_at`) e `prices` (`source` = live ou
  wayback). Um preço por produto por dia (dia no fuso de Brasília); a última coleta do dia substitui as anteriores.
  `prices` é ordenada por dia (`primary key(day, product_id, source)`, without rowid): cada coleta só acrescenta no
  fim do arquivo, e o .db pesa menos no histórico do git. `db()` migra bancos antigos sozinho. Ficar de olho no
  tamanho do repositório (`git count-objects -vH`); perto de 1 GB, migrar o histórico para o Cloudflare D1.
- `.github/workflows/relogio.yml` ("Relógio da coleta"): o `schedule` do GitHub nunca disparou neste repositório
  (25-26/11), então este job fica de plantão, dispara o `coletar.yml` quando a última coleta tem 3 h ou mais e se
  re-dispara perto do limite de 6 h. Se parar, religar em Actions → Run workflow. Desligar = cancelar a execução.
- `.github/workflows/coletar.yml`: KaBuM! a cada 3h; domingo às 9h também busca histórico. Para rodar na mão:
  `gh workflow run "Coletar preços" -f historico=sim -f meses=4`.
- `.github/workflows/testar-loja.yml` ("Testar loja", input `loja`): coleta uma loja numa cópia na rede do GitHub.
- `.github/workflows/testar-lojas.yml`: teste rápido para ver se as lojas respondem ao robô do GitHub (não salva nada).
- Os robôs fazem commit de `data.js` e do `.db` várias vezes por dia: **sempre rode `git pull` antes de mexer**.

## Cupons (janela do produto)
- `collector/cupons.py`: junta `data/cupons.json` (cupons à mão, ex.: exclusivo que uma loja mandou) e
  `data/cupons-auto.json` (comando `cupons`, Lomadee, só marcas ligadas a uma loja do site pela chave `"lomadee"` da
  loja na watchlist). O `exportar` põe os válidos em `data.js` (`cupons`). Formato no topo de `cupons.py`.
- No site: selo "CUPOM DE DESCONTO" no cartão, botão "Cupom de desconto" (primeiro da barra, borda azul→verde do logo, com o nº de ofertas), caixa "Cupom de desconto do Muquirana" na janela com "Copiar cupom e ver o produto na loja"
  (copia o código e abre o MESMO link do "Ver na loja", na página do produto; não o link genérico do cupom). "Preço com cupom (estimado)" só com `pct`/`valor` e compra mínima atingida. O Muquirômetro e a Black
  Fraude julgam o preço SEM cupom. Sem cupom válido, nada aparece. Nunca inventar cupom nem mostrar cupom de loja que
  não está no site (o dono não quer página genérica de cupons).

## Parcelamento e "Apoie o Muquirana"
- `collector/parcelas.py`: parcelamento no cartão `{"n","v","total","juros"}` guardado na coluna `products.parcelas`
  e exportado como `parc`. KaBuM! (`maxInstallment`, sem juros quando o total bate com o preço no cartão),
  Samsung/Motorola (VTEX `Installments`: maior parcela sem juros num cartão comum), Lenovo (o mesmo da ficha).
  Amazon, Kalunga e jogos: não mostra nada. Nunca inventar parcelamento. No site: linha abaixo do preço (cartão e janela).
- Lenovo pela Lomadee: qualquer link (deep link ou encurtador "Custom") abre a página INICIAL (a Lomadee confirmou em
  27/11; a comissão vale para qualquer compra na latência do cookie). A pedido do dono, o próprio "Ver na Lenovo"
  usa o link de afiliado (`STORES.lenovo.apoio`, `mdasc=site`): copia o código do produto e mostra a dica "cole na busca
  da Lenovo". No cartão, "Ver na loja" da Lenovo abre a janela (onde está a dica). Nunca abrir link de afiliado escondido.

## Muquirômetro (termômetro, sem nota e sem descrição)
Faixa pelo quanto o preço de hoje está acima do menor preço já visto (`up`):
- Até o Muquirana compra: até 2% acima
- Muquirana aprova: até 10%
- Segura a carteira: até 30%
- Cilada!: acima de 30%
- Muquirana de olho: produto com menos de 30 dias de histórico

## Black Fraude × Black Firmeza
Preço normal = mediana dos preços de 31 a 90 dias atrás (`BF` em `index.html`).
- **Black Fraude**: hoje não está nem 3% abaixo do normal E (subiu 8% ou mais nos últimos 30 dias, OU o preço "de"
  promete 25% ou mais de desconto). Usamos 25% porque a KaBuM! já dá até 15% de desconto no Pix em tudo.
- **Black Firmeza**: 8% ou mais abaixo do preço normal.
- Os selos nunca contradizem o termômetro: Fraude só com "Segura a carteira"/"Cilada!" (mais de 10% acima do menor
  já visto); Firmeza só com "Compra"/"Aprova". Preço bom com "de" inflado ganha só um aviso amarelo (`deInflado`).

## Preço sempre atual
- `exportar` deixa fora do site produto cujo preço não foi conferido nas últimas 36 h (`checked_at`).
- O site esconde produto cuja oferta relâmpago (`ends`) já acabou, até a próxima coleta trazer o preço novo.
- `data.js` é carregado com `?v=` que muda a cada 5 minutos (o navegador não reaproveita preço velho).
- O dono pediu para NÃO mostrar a hora da última atualização no topo nem no rodapé (26/11); a hora em que o preço
  foi visto fica só na janela do produto.

## Lojas (testes de 25/11/2026)
| Loja | Situação |
|---|---|
| KaBuM! | ✅ GitHub (vendedores KaBuM!, Magalu e Fast Shop) |
| Amazon | ✅ só pelo PC do dono (bloqueia o GitHub). No futuro: API oficial via Programa de Associados |
| Mercado Livre | ⏸️ em espera (26/11): o botão "Criar nova aplicação" fica desabilitado na conta do dono, mesmo com os dados completos; o site manda robôs (até do PC) para "verificação de conta". Código e `testar-mercadolivre.yml` prontos para quando liberar |
| Americanas | ❌ a API VTEX responde 400 "Scripts are not allowed" na rede do GitHub (26/11); sem preço confiável, não coletamos |
| Steam | ✅ API pública (`store.steampowered.com/api/storesearch`), não implementada ainda |
| Kalunga | ✅ GitHub (HTML da busca + preço à vista da ficha do produto) |
| Samsung | ✅ `collector/samsung.py`: API pública VTEX (`shop.samsung.com/br/api/catalog_system`), categorias de tecnologia inteiras, preço do Pix, só seller "1" (a Samsung), sem kits "A + B" |
| Carrefour | ⏳ só o PC do dono passa (GitHub 403); coletor ainda não feito |
| PlayStation Store | ✅ GitHub, com navegador (Playwright, job `coletar-navegador`); 20 jogos, 5 preços conferidos |
| Motorola | ✅ `collector/motorola.py`: API pública VTEX (`www.motorola.com.br/api/catalog_system`), categoria Smartphones, preço do Pix, só seller "1" |
| Lenovo | ✅ `collector/lenovo.py`: API das páginas de categoria (`openapi.lenovo.com`, filtro `pageFilterId`) para a lista e `/detail/price/batch/get` (a da ficha) para o preço do Pix; notebooks, desktops e monitores. `/search` é proibido no robots.txt |
| PCYes | ✅ `collector/pcyes.py`: 1ª página (12 itens) de cada categoria do sitemap, `__NEXT_DATA__` (Magento), `final_price` = preço da ficha (Pix = cartão em 10x sem juros); `/graphql` e `/search` proibidos. ~200 produtos. Link de comissão Lomadee (abre o produto) |
| Concórdia Informática | ✅ `collector/concordia.py`: páginas de categoria Tray (`?pg=N`), preço "à vista com desconto" (igual à ficha); esgotados ficam por último e o coletor para; sem Outlet nem automação comercial. ~380 produtos. Link de comissão Lomadee (abre o produto) |
| Xiaomi (Mi Brasil) | ✅ `collector/xiaomi.py`: `/products.json?pg=N` (Linx, catálogo inteiro, 15 por página; `/produtos` e `/pesquisa` proibidos no robots.txt), preço "Por ... à vista" (`BestInstallment` em 1x com desconto) = ficha, parcelamento `MaxInstallmentsNoInterest`; categoria do site pela categoria da loja (`CATS`), sem capas, películas, peças de reposição, beleza e pet. ~137 produtos, 8 de 8 preços iguais à ficha (27/11). Na Lomadee: "Dl Comercio E Industria De Produtos Eletronicos" (2,38%); link de comissão abre o produto |
| Shopinfo | ❌ Shopify limita robôs (429 depois de 3-4 acessos); deep link da Lomadee funciona: só com feed oficial |
| Xbox Store | ✅ `collector/xbox.py` (navegador, job `coletar-navegador`), 20 jogos, 5 preços conferidos (26/11) |
| Apple, Dell | ⏳ responderam à sondagem de 26/11 no GitHub; coletores pendentes (tarefa 5d); Apple deixada de lado |
| Magalu, Casas Bahia, Pichau, Terabyte, Nuuvem, LG | ❌ 403/captcha para robôs (Pichau/Terabyte só abrem no PC com navegador). Não burlar: só por afiliados/feeds oficiais (Awin em análise; Lomadee tem TeraByte e Lenovo, sem feed de produtos) |

## Infra
- Repositório: https://github.com/renanmazzeo/muquiranatech (público). GitHub CLI: `C:\Program Files\GitHub CLI\gh.exe`.
- Site principal: https://muquiranatech.com.br (domínio no registro.br, expira 26/11/2027; DNS no Cloudflare; `www` também funciona).
  E-mail público: contato@muquiranatech.com.br (Cloudflare Email Routing → Gmail do projeto).
- Afiliados: Lomadee (canal `muquirana-tech`, secret `LOMADEE_API_KEY`, workflow "Testar Lomadee"; deep link
  `https://lmdee.link/deep/muquirana-tech?url=<url codificada>` só funciona depois que o canal for aprovado; em 26/11
  ainda dava `channel_not_found`). Awin em análise. Quando ligar link de afiliado, usar `rel="sponsored"` e trocar o
  "poderão" de privacidade.html e como-funciona.html.
  Endereço técnico do Cloudflare Pages: https://muquiranatech.pages.dev (conectado ao GitHub, publica a cada push).
  Também em https://renanmazzeo.github.io/muquiranatech/ (GitHub Pages).
  Cloudflare grátis: 500 builds por mês. Os robôs fazem cerca de 360 (KaBuM! a cada 3h + Amazon a cada 6h).
  **Não aumente a frequência**, e pull requests também geram builds de prévia.
  A Netlify foi descartada porque o plano grátis novo só permite cerca de 20 deploys por mês.
- Banco: SQLite no git basta por enquanto. Quando o repositório passar de cerca de 1 GB, migrar para o Cloudflare D1.
