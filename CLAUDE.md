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
- `collector/muq.py`: comandos
  - `coletar [--lojas kabum,amazon]`: preço de hoje. Cada loja usa a `pausa` definida para ela na watchlist.
  - `historico --meses N` (padrão 12, nunca mais de 1 ano), `--max-minutos`: Wayback, só KaBuM!. Baixa primeiro
    as cópias mais recentes e pula as que já baixou (tabela `wayback_done`).
  - `mesclar <copia.db> --lojas X [--wayback]`: junta no banco real só as linhas da loja X vindas de uma cópia.
  - `exportar`: gera `data.js` (sempre com fim de linha LF).
  - `MUQ_DB=<arquivo>`: faz qualquer comando usar outro banco. Os robôs coletam numa cópia e só no fim fazem
    `git fetch` + `reset` + `mesclar` + `exportar` + push. Assim um robô nunca apaga a coleta do outro.
- `collector/kabum.py`: lê o `__NEXT_DATA__` das buscas da KaBuM!. **Ofertas:** em promoções o preço real fica em
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
- `collector/watchlist.json`: `lojas` (nome, vendedores confiáveis, `not` e `pausa` por loja) e 112 `buscas`
  comuns (`q`, `cat`, `must`, `not`, `max`), com ajustes por loja (ex.: `"amazon": {"must": [...]}` ou
  `{"skip": true}`). Antes de adicionar uma busca, teste o `search` + `pick` e confira se o produto bate com o nome.
- `data/muquirana.db`: SQLite. `products` (inclui `offer_ends` e `checked_at`) e `prices` (`source` = live ou
  wayback). Um preço por produto por dia (dia no fuso de Brasília); a última coleta do dia substitui as anteriores.
- `.github/workflows/coletar.yml`: KaBuM! a cada 3h; domingo às 9h também busca histórico. Para rodar na mão:
  `gh workflow run "Coletar preços" -f historico=sim -f meses=4`.
- `.github/workflows/testar-lojas.yml`: teste rápido para ver se as lojas respondem ao robô do GitHub (não salva nada).
- Os robôs fazem commit de `data.js` e do `.db` várias vezes por dia: **sempre rode `git pull` antes de mexer**.

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

## Lojas (testes de 25/11/2026)
| Loja | Situação |
|---|---|
| KaBuM! | ✅ GitHub (vendedores KaBuM!, Magalu e Fast Shop) |
| Amazon | ✅ só pelo PC do dono (bloqueia o GitHub). No futuro: API oficial via Programa de Associados |
| Mercado Livre | ⏳ só pela API oficial; o dono precisa criar o app em developers.mercadolivre.com.br |
| Americanas | ❌ a API VTEX responde 400 "Scripts are not allowed" na rede do GitHub (26/11); sem preço confiável, não coletamos |
| Steam | ✅ API pública (`store.steampowered.com/api/storesearch`), não implementada ainda |
| Kalunga | ✅ GitHub (HTML da busca + preço à vista da ficha do produto) |
| Carrefour | ⏳ só o PC do dono passa (GitHub 403); coletor ainda não feito |
| Samsung, Apple, Dell, Lenovo, Motorola, PlayStation, Xbox | ⏳ responderam à sondagem de 26/11 no GitHub; coletores pendentes (tarefa 5d) |
| Magalu, Casas Bahia, Pichau, Terabyte, Nuuvem, LG | ❌ 403/captcha para robôs (Pichau/Terabyte só abrem no PC com navegador) |

## Infra
- Repositório: https://github.com/renanmazzeo/muquiranatech (público). GitHub CLI: `C:\Program Files\GitHub CLI\gh.exe`.
- Site principal: https://muquiranatech.pages.dev (Cloudflare Pages, conectado ao GitHub, publica a cada push).
  Também em https://renanmazzeo.github.io/muquiranatech/ (GitHub Pages).
  Cloudflare grátis: 500 builds por mês. Os robôs fazem cerca de 360 (KaBuM! a cada 3h + Amazon a cada 6h).
  **Não aumente a frequência**, e pull requests também geram builds de prévia.
  A Netlify foi descartada porque o plano grátis novo só permite cerca de 20 deploys por mês.
- Banco: SQLite no git basta por enquanto. Quando o repositório passar de cerca de 1 GB, migrar para o Cloudflare D1.
