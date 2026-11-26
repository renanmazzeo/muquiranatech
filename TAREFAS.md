# Tarefas do agente autônomo

Este arquivo é o roteiro do agente que roda sozinho (tarefa agendada do Claude Code na nuvem).
Cada execução começa do zero: tudo o que o agente precisa saber está aqui, no [CLAUDE.md](CLAUDE.md) e no
[DIARIO.md](DIARIO.md).

## Como cada execução funciona
1. Leia o CLAUDE.md, este arquivo e as **3 últimas entradas** do DIARIO.md.
2. Veja se algum pull request seu ainda está aberto (`gh pr list --author @me`):
   - se o dono comentou pedindo mudança, atenda **isso primeiro**, no mesmo branch;
   - **no máximo 3 PRs seus abertos ao mesmo tempo**. Se já houver 3, só faça a tarefa 0 (saúde) e encerre.
3. Faça a **tarefa 0** (sempre) e depois **uma** tarefa da fila: a primeira com status `[ ]` cujo pré-requisito
   esteja cumprido. Tarefa grande demais para uma execução? Quebre em partes e entregue só a primeira.
4. Registre a execução no DIARIO.md (modelo no fim daquele arquivo) e atualize o status da tarefa aqui.
5. Pare. Não emende outra tarefa: o dono revisa um PR de cada vez.

## Regras (não negociáveis)
- **Nunca faça push na `main`.** Trabalhe num branch `agente/<tarefa>` e abra um pull request em português,
  explicando em linguagem simples o que muda para quem usa o site e como você testou.
- O registro no DIARIO.md e a mudança de status neste arquivo vão **no mesmo PR** da tarefa. Numa execução
  sem PR (só a tarefa 0, ou só um problema registrado), abra um PR pequeno só com o diário.
- **Nunca altere** `data/muquirana.db` nem `data.js`: são dos robôs de coleta. Se seu branch tocar neles, desfaça.
- **Nunca mexa** em credenciais, segredos, no `coletar-pc.ps1` agendado no PC do dono, nem nas configurações da
  Cloudflare ou do GitHub (Pages, secrets, branch protection).
- **Nunca aumente** a frequência dos robôs: o plano grátis da Cloudflare tem 500 builds por mês.
- **Requisições às lojas:** no máximo 20 por execução, com 3 s ou mais entre elas. **Nunca acesse a Amazon** (ela
  bloqueia IPs de servidor, e insistir pode atrapalhar a coleta do PC do dono).
- Serviço pago, cadastro em site, aceitar termos, qualquer coisa em nome do dono: **não faça**. Anote no
  DIARIO.md em "Precisa do dono".
- Ficou em dúvida sobre o que o dono quer? Escolha a opção mais conservadora e pergunte no PR.
- Teste antes de abrir o PR. Python: `python -I -c "import ast; ast.parse(...)"` e os testes em `tests/` quando
  existirem. Site: abra o `index.html` no Chrome headless, se houver, e confira que não aparece erro no console.
- Commits terminam com `Co-Authored-By: Claude <noreply@anthropic.com>`.

---

## Tarefa 0: saúde dos robôs (toda execução, leva poucos minutos)
- `data.js`: o campo `gerado` tem menos de 6 horas? Os produtos `kabum:` aparecem? E os `amazon:`?
  Produtos da Amazon somem do `data.js` depois de 7 dias sem coleta, então se eles faltam, o robô do PC parou.
- `gh run list --workflow coletar.yml -L 5`: alguma execução terminou em `failure`? (`cancelled` feito à mão não
  é problema.) Se houver falha, leia o log (`gh run view <id> --log-failed`).
- Problema achado: tente corrigir na tarefa desta execução, com PR. Se não der (por exemplo, a Amazon parada,
  que depende do PC do dono), registre em "Precisa do dono" no DIARIO.md e siga para a fila.

## Fila (em ordem de prioridade)

### 1. [ ] Testes automáticos dos leitores de loja
Por quê: se a KaBuM! mudar o formato das páginas, hoje só descobrimos quando o site mostra preço errado.
- Crie `tests/` com páginas salvas (fixtures pequenas, cortando o que não interessa) da KaBuM!, incluindo um
  produto **com oferta ativa** e um **sem oferta**, e uma página de busca da Amazon. A página da Amazon **não pode
  ser baixada pelo agente**: monte um HTML mínimo com a mesma estrutura que o `amazon.parse()` espera.
- Testes com `unittest` (sem dependências novas): `kabum.parse` usa o preço da oferta só dentro de
  `startsAt..endsAt`; `pick` respeita `must`, `not` e vendedores; `amazon.parse` ignora patrocinados e lê o
  preço atual e o riscado; `mesclar` não duplica nada e não apaga a outra loja.
- Workflow `.github/workflows/testes.yml` rodando os testes em cada pull request.
- Pronto quando: `python -m unittest` passa localmente e no PR.

### 2. [ ] Steam como loja (jogos de PC)
Por quê: mais lojas confiáveis e mais produtos. A API da Steam é pública e funciona do GitHub.
- `collector/steam.py` no mesmo formato do `kabum.py`: `storesearch/?term=...&cc=br&l=portuguese` e, para o preço
  com desconto, `api/appdetails?appids=...&cc=br&filters=price_overview`. O preço já vem em centavos de real.
- Vendedor: "Steam" (confiável). Categoria `game`. Só os jogos mais procurados: crie na watchlist uma lista
  própria de buscas para a Steam (cerca de 20 jogos populares) com `{"skip": true}` nas buscas que não fazem
  sentido para ela.
- Inclua `steam` em `LOJAS` no `muq.py` e em `STORES` no `index.html` (cor `#1b2838`, domínio
  `store.steampowered.com`). Adicione `--lojas kabum,steam` no `coletar.yml`, mantendo a mescla por loja.
- Pronto quando: uma coleta local com `--lojas steam` traz cerca de 20 jogos com preço igual ao da página da Steam
  (confira 5).

### 3. [ ] Lista de produtos que carrega aos poucos
Por quê: já são cerca de 580 produtos, e o celular fica pesado desenhando tudo de uma vez.
- Mostre 48 cards e um botão "Mostrar mais" (mais 48 por clique). Filtros, busca e ordenação continuam valendo
  sobre a lista inteira. O contador mostra o total encontrado.
- A busca deve ignorar acentos e maiúsculas ("memoria" acha "Memória").
- Pronto quando: abrir o site no Chrome headless em 390 px de largura não dá erro, e "Mostrar mais" funciona.

### 4. [ ] Página "Como funciona" e mais credibilidade
Por quê: o leigo precisa entender de onde vêm os preços para confiar.
- Seção ou janela "Como o Muquirana funciona", ligada a partir do rodapé e do topo: de onde vêm os preços (lojas
  e vendedores aceitos), de quanto em quanto tempo atualiza, o que é o preço à vista no Pix, como funcionam o
  Muquirômetro e a Black Fraude (com os números do CLAUDE.md), e o aviso "confira sempre na loja".
- `<meta name="description">`, Open Graph (`og:title`, `og:description`, `og:image`) e um favicon em SVG inline,
  para o link ficar bonito quando compartilhado no WhatsApp.
- Pronto quando: o texto está em português simples, sem jargão, e os números batem com o código.

### 5. [ ] Detector de produto errado
Por quê: às vezes uma busca traz o item errado (já apareceram pilhas no lugar de controle de Xbox).
- Script `collector/revisar.py` que lê o `data.js` e lista suspeitos: preço muito fora da mediana da categoria
  (menos de 25% ou mais de 400%), nome sem nenhuma palavra do `must` da busca, ou nome de acessório (capa,
  película, suporte, cabo, pilha) em categoria de aparelho.
- Use a lista para propor no PR ajustes de `must`/`not` na watchlist. **Não remova buscas inteiras** sem explicar.
- Pronto quando: o script roda e o PR traz a lista do que foi encontrado e do que foi ajustado.

### 6. [ ] Revisão da Black Fraude com dados reais
Pré-requisito: pelo menos 35 dias de histórico ao vivo, ou o histórico da Wayback já coletado.
- Liste os produtos que caem em Black Fraude e Black Firmeza. Para cada Black Fraude, confira no gráfico se o
  aumento é real ou ruído (por exemplo, um dia isolado sem oferta).
- Se houver falsos positivos, proponha ajustes nas regras (`BF` no `index.html`), com exemplos no PR.
  **Não mude os números sem mostrar exemplos.**

### 7. [ ] Reteste mensal das lojas bloqueadas
- Uma vez por mês (veja no DIARIO.md quando foi o último): rode o workflow `testar-lojas.yml` adaptado para
  Americanas, Carrefour, Magalu, Casas Bahia, Pichau e Terabyte, com 1 requisição por loja.
- Registre o resultado no DIARIO.md e atualize a tabela "Lojas" do CLAUDE.md. Se alguma abrir, crie uma tarefa
  nova aqui para ela, em vez de implementar na hora.
- Esta tarefa volta para `[ ]` todo mês.

## Precisa do dono (o agente não faz)
- **Mercado Livre:** criar o app em developers.mercadolivre.com.br e guardar o ID e a chave como secrets do GitHub.
- **Amazon:** cadastrar-se no Programa de Associados (comissão por venda e, depois de 3 vendas, a API oficial, que
  permitiria coletar a Amazon pelo GitHub sem depender do PC).
- **Cloudflare:** desligar os builds de prévia de branches (Settings → Builds → Branch control → só `main`), para
  os PRs do agente não gastarem o limite de 500 builds por mês.
- **Domínio próprio:** opcional, cerca de R$ 40 por ano no Registro.br.
