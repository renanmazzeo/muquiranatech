# MuquiranaTech: contexto do projeto

Portal de ofertas de tecnologia que compara o preço de hoje com o histórico, só com vendedores confiáveis.
Público: leigo em tecnologia. Todo o texto do site é em português do Brasil.

## Regras do dono
- **Só serviços gratuitos.** Hospedagem, banco de dados e automação precisam ter plano grátis que aguente o uso.
- Mostrar no computador antes de publicar mudanças grandes no site. Todo push na `main` vai ao ar no GitHub Pages.
- O site precisa transmitir credibilidade: dados reais, data da última atualização, só lojas e vendedores confiáveis.

## Como funciona
- `index.html`: o site inteiro (HTML, CSS e JS num arquivo só). Lê `data.js`; sem ele, mostra dados fictícios.
- `collector/muq.py`: comandos `coletar`, `historico`, `exportar` e `tudo`.
  - `historico --meses N` (padrão 12, nunca mais de 1 ano), `--max-minutos` para parar antes do limite do GitHub.
  - Baixa primeiro as cópias mais recentes da Wayback e pula as que já baixou (tabela `wayback_done`).
- `collector/kabum.py`: lê o `__NEXT_DATA__` das páginas de busca da KaBuM!. `pick()` filtra por vendedor
  confiável, disponibilidade, palavras obrigatórias (`must`) e proibidas (`not`).
- `collector/watchlist.json`: 112 buscas (cerca de 300 produtos). Para testar uma busca nova, rode `kabum.search` e
  `kabum.pick` antes de adicionar e confira se o produto bate com o nome.
- `data/muquirana.db`: SQLite (`products`, `prices` com `source` live ou wayback). Um preço por produto por dia;
  a coleta das 18h substitui a das 6h.
- `.github/workflows/coletar.yml`: coleta às 6h e às 18h (horário de Brasília); domingo às 9h também busca histórico.
  Rodar na mão: `gh workflow run "Coletar preços" -f historico=sim -f meses=4`.
  O robô faz commit de `data.js` e do `.db`: sempre rode `git pull` antes de mexer.

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

## Fontes
- KaBuM!: funciona (vendedores KaBuM!, Magalu e Fast Shop).
- Wayback Machine: histórico.
- Mercado Livre: falta criar as credenciais do app na API (necessário para Xbox, Xiaomi, Meta Quest e pendrives, que
  na KaBuM! só têm vendedores pequenos).
- Pichau, Terabyte e Magalu bloqueiam robôs; avaliar programas de afiliado.

## Infra
- Repositório: https://github.com/renanmazzeo/muquiranatech (público). GitHub CLI em `C:\Program Files\GitHub CLI\gh.exe`.
- Site: https://renanmazzeo.github.io/muquiranatech/ (GitHub Pages, branch `main`).
- Próximo passo combinado: publicar no **Cloudflare Pages** (`muquiranatech.pages.dev`). O dono já criou a conta.
  A Netlify foi descartada porque o plano grátis novo só permite cerca de 20 deploys por mês, e o robô faz cerca de 60.
- Banco: SQLite no git basta por enquanto. Quando o repositório passar de cerca de 1 GB, migrar para o Cloudflare D1
  (grátis, 5 GB).

## Pendências
- Conferir o resultado do primeiro histórico da Wayback (4 meses) e se a Black Fraude flagrou produtos de verdade.
- Publicar no Cloudflare Pages.
- Integrar o Mercado Livre.
- Domínio próprio (.com.br, cerca de R$ 40 por ano no Registro.br) é opcional e fica para o futuro.
