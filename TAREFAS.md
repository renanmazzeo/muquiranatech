# Tarefas do agente autônomo

Este arquivo é o roteiro do agente que roda sozinho (tarefa agendada do Claude Code na nuvem).
Cada execução começa do zero: tudo o que o agente precisa saber está aqui, no [CLAUDE.md](CLAUDE.md) e no
[DIARIO.md](DIARIO.md).

## Objetivo, e quando parar
O agente existe **só para terminar a construção do projeto**: deixar o site completo e testado, com os preços de
**todas as lojas que for possível coletar**. Não é manutenção diária.
- Quando todas as tarefas abaixo estiverem `[x]` ou `[-]` (impossível, com o motivo), faça a **tarefa final**.
- A tarefa final troca a linha `ESTADO:` do DIARIO.md para `ESTADO: CONCLUÍDO`.
- **Se o DIARIO.md já diz `ESTADO: CONCLUÍDO`, não faça nada: encerre a execução imediatamente.**

## Como cada execução funciona
1. Leia o CLAUDE.md, este arquivo e as **3 últimas entradas** do DIARIO.md. Confira a linha `ESTADO:`.
2. Veja seus pull requests abertos (`gh pr list --author @me`):
   - se o dono comentou pedindo mudança, atenda **isso primeiro**, no mesmo branch;
   - **no máximo 3 PRs seus abertos ao mesmo tempo**. Se já houver 3, só faça a checagem de saúde e encerre.
3. Faça a **checagem de saúde** e depois **uma** tarefa: a primeira com `[ ]` cujo pré-requisito esteja
   cumprido. Tarefa grande demais para uma execução? Entregue uma parte que funcione sozinha e marque `[~]`
   (em andamento), dizendo no DIARIO.md o que falta.
4. Registre a execução no DIARIO.md (modelo no fim daquele arquivo) e atualize o status da tarefa aqui.
5. Pare. Não emende outra tarefa: o dono revisa um PR de cada vez.

Status: `[ ]` a fazer · `[~]` em andamento · `[x]` feita (PR aceito) · `[-]` impossível (motivo no DIARIO.md).
Uma tarefa só vira `[x]` quando o PR dela foi aceito. Enquanto o PR estiver aberto, deixe `[~]` e siga para a
próxima, se não depender dela.

## Regras (não negociáveis)
- **Nunca faça push na `main`.** Trabalhe num branch `agente/<tarefa>` e abra um pull request em português,
  explicando em linguagem simples o que muda para quem usa o site e como você testou.
- O registro no DIARIO.md e a mudança de status neste arquivo vão **no mesmo PR** da tarefa.
- **Nunca altere** `data/muquirana.db` nem `data.js`: são dos robôs de coleta. Se seu branch tocar neles, desfaça.
- **Nunca mexa** em credenciais ou segredos, no `coletar-pc.ps1`, nem nas configurações da Cloudflare ou do
  GitHub (Pages, secrets, branch protection).
- **Nunca aumente** a frequência dos robôs: o plano grátis da Cloudflare tem 500 builds por mês.
- **Requisições às lojas:** no máximo 30 por execução, com 3 s ou mais entre elas. **Nunca acesse a Amazon** (ela
  bloqueia IPs de servidor, e insistir pode atrapalhar a coleta do PC do dono).
- **Só serviços gratuitos.** Serviço pago, cadastro em site, aceitar termos, qualquer coisa em nome do dono:
  **não faça**. Anote no DIARIO.md em "Precisa do dono".
- Ficou em dúvida sobre o que o dono quer? Escolha a opção mais conservadora e pergunte no PR.
- **Preço tem que ser igual ao da loja.** Toda loja nova precisa, antes do PR, de uma conferência de 5 produtos:
  o preço que o coletor lê contra o preço que a página do produto mostra (à vista/Pix). Se não bater, não publique
  a loja: explique no PR. Foi assim que pegamos o bug das ofertas da KaBuM! em 25/11.
- **Só vendedores confiáveis:** a própria loja ou lojas oficiais das marcas. Nada de marketplace genérico.
- Teste antes de abrir o PR: `python -m unittest` (depois da tarefa 1) e, no site, o `index.html` no Chrome
  headless (se houver) a 1320 px e a 390 px de largura, sem erro no console.
- Commits terminam com `Co-Authored-By: Claude <noreply@anthropic.com>`.

---

## Checagem de saúde (toda execução, poucos minutos)
- `data.js`: o campo `gerado` tem menos de 6 horas? Quantos produtos há de cada loja (prefixo do `id`)?
- `gh run list --workflow coletar.yml -L 5`: alguma execução terminou em `failure`? (`cancelled` feito à mão não
  é problema.) Se houver, leia o log com `gh run view <id> --log-failed`.
- Produtos `amazon:` sumiram? Então o robô do PC parou, e isso só o dono resolve: anote em "Precisa do dono".
- Anote os números na entrada do DIARIO.md. Se houver falha de coleta, corrigir vira a tarefa desta execução.

## Tarefas

### 1. [ ] Testes automáticos dos leitores de loja
Por quê: sem testes, só descobrimos que uma loja mudou o formato quando o site mostra preço errado.
- Crie `tests/` com páginas salvas (fixtures pequenas, cortando o que não interessa) da KaBuM!, incluindo um
  produto **com oferta ativa** e um **sem oferta**. Para a Amazon, **não baixe nada**: monte um HTML mínimo
  com a estrutura que o `amazon.parse()` espera (resultado normal, patrocinado, preço riscado).
- Testes com `unittest` (sem dependências novas): a oferta da KaBuM! só vale dentro de `startsAt..endsAt`;
  `pick` respeita `must`, `not` e vendedores; `amazon.parse` ignora patrocinados; `mesclar` não duplica e não
  apaga a outra loja.
- Workflow `.github/workflows/testes.yml` rodando os testes em cada pull request.
- Pronto quando: `python -m unittest` passa localmente e no PR.

### 2. [ ] Steam (jogos de PC)
API pública, funciona do GitHub.
- `collector/steam.py` no mesmo formato do `kabum.py`: `store.steampowered.com/api/storesearch/?term=...&cc=br&l=portuguese`
  e, para o preço, `api/appdetails?appids=...&cc=br&filters=price_overview` (valores em centavos de real).
- Vendedor "Steam". Categoria `game`. Uma lista própria de cerca de 20 jogos populares de PC. Nas buscas que não
  fazem sentido para a Steam, use `{"skip": true}`.
- Inclua `steam` em `LOJAS` (`muq.py`), em `STORES` (`index.html`, cor `#1b2838`, domínio `store.steampowered.com`)
  e no `coletar.yml` (`--lojas kabum,steam`, mescla com `--lojas kabum,steam`).
- Pronto quando: a coleta local com `--lojas steam` traz cerca de 20 jogos e 5 conferidos batem com a Steam.

### 3. [ ] Mercado Livre (API oficial), deixar pronto para ligar
O dono ainda vai criar o app. O agente deixa tudo pronto para funcionar no dia em que os secrets existirem.
- `collector/mercadolivre.py`: token por `client_credentials` (`ML_CLIENT_ID` e `ML_CLIENT_SECRET` vindos de
  variáveis de ambiente) e busca em `api.mercadolibre.com/sites/MLB/search`. **Só lojas oficiais**
  (`official_store_id` preenchido) e itens novos. Preço: `price` do resultado.
- No `coletar.yml`, passe os secrets como variáveis de ambiente; sem eles, o coletor pula o Mercado Livre e
  escreve uma linha no log, sem falhar.
- Em `STORES` no site, a entrada `ml` já existe.
- Um guia curto em português no PR: como o dono cria o app (developers.mercadolivre.com.br) e cadastra os dois
  secrets no GitHub (Settings → Secrets and variables → Actions).
- Pronto quando: os testes com uma resposta de exemplo da API passam e o workflow roda sem erro sem os secrets.
  A tarefa fica `[x]` mesmo sem as credenciais; ligar de verdade fica em "Precisa do dono".

### 4. [ ] Americanas
- A API VTEX pública responde: `americanas.com.br/api/catalog_system/pub/products/search?ft=...`.
- Problemas vistos em 25/11: a busca traz itens de outras categorias (pede-se "smart tv 55" e vem rack), e o preço
  à vista na página pode ser diferente do `Price` da API (desconto no Pix).
- Use só vendedor `AMERICANAS SA` com `AvailableQuantity > 0`, e `must`/`not` para tirar itens errados.
  Descubra de onde vem o preço à vista que a página mostra (outro campo da API, `Installments` com Pix, ou o
  HTML do produto) e confira 5 produtos.
- Se o preço não bater de jeito nenhum, marque `[-]` e explique no DIARIO.md.

### 5. [ ] Lojas que bloqueiam robôs: tentar navegador de verdade
Magalu, Casas Bahia, Pichau, Terabyte e Carrefour devolvem 403/captcha para `requests`.
- Crie um workflow de teste (sem salvar dados) que usa **Playwright com Chromium** (grátis) no GitHub Actions e
  abre **uma** busca de cada loja. Registre quais mostram produtos com preço.
- Para cada loja que funcionar: crie uma tarefa nova aqui (no padrão das tarefas 2 e 4), em vez de implementar
  tudo na mesma execução.
- As que não funcionarem: `[-]` com o motivo, e atualize a tabela "Lojas" do CLAUDE.md.
- Nada de serviço pago de proxy ou de resolver captcha.

### 6. [ ] Site com muitas lojas e muitos produtos
- Lista que carrega aos poucos: 48 cards e um botão "Mostrar mais". Filtros, busca e ordenação valem sobre a
  lista inteira, e o contador mostra o total.
- A busca ignora acentos e maiúsculas ("memoria" acha "Memória").
- Filtro de lojas com o logo e a quantidade de produtos de cada loja.
- O mesmo produto em lojas diferentes: quando o nome normalizado for praticamente igual (mesmo modelo), mostrar na
  ficha "Também em: Amazon R$ X". Comece conservador: só quando houver um código de modelo igual no nome
  (ex.: "VG279QM5F"), para não juntar produtos diferentes.
- Pronto quando: funciona a 390 px e a 1320 px no Chrome headless, sem erro no console.

### 7. [ ] "Como funciona" e credibilidade
- Uma seção ou janela "Como o Muquirana funciona", ligada a partir do topo e do rodapé: de onde vêm os preços
  (lojas e vendedores aceitos), de quanto em quanto tempo atualiza, o preço à vista no Pix, como funcionam o
  Muquirômetro e a Black Fraude (com os números do CLAUDE.md) e o aviso "confira sempre na loja".
- `<meta name="description">`, Open Graph (`og:title`, `og:description`, `og:image`) e um favicon SVG inline,
  para o link ficar bonito no WhatsApp.
- Pronto quando: o texto está em português simples, sem jargão, e os números batem com o código.

### 8. [ ] Qualidade dos dados
- Script `collector/revisar.py` que lê o `data.js` e lista suspeitos: preço muito fora da mediana da categoria
  (menos de 25% ou mais de 400%), nome sem nenhuma palavra do `must` da busca, ou acessório (capa, película,
  suporte, cabo, pilha) em categoria de aparelho.
- Corrija a watchlist com `must`/`not` a partir da lista. **Não remova buscas inteiras** sem explicar no PR.
- Pronto quando: o script roda e o PR traz o que foi encontrado e o que foi ajustado.

### 9. [ ] Tarefa final: revisão geral e encerramento
Só quando todas as tarefas acima estiverem `[x]` ou `[-]`.
- Abra o site no Chrome headless a 390 px e a 1320 px, com os dados atuais, e confira: todas as lojas ativas
  aparecem, ficha do produto, Black Fraude, filtros, "Mostrar mais" e "Como funciona".
- Atualize o README.md (o que é, lojas, como rodar) e o CLAUDE.md (arquitetura e tabela de lojas).
- No DIARIO.md: um resumo final do que ficou pronto, do que ficou impossível e do que depende do dono, e
  `ESTADO: CONCLUÍDO`.
- No PR, peça ao dono que desligue o agendamento em https://claude.ai/code/routines.

## Fora do escopo do agente
Ficam para o dono, ou para uma conversa com o Claude depois:
- revisar as regras da Black Fraude com dados reais (precisa de mais de 35 dias de histórico);
- retestar lojas bloqueadas no futuro;
- domínio próprio, Programa de Associados da Amazon, alertas de preço.
