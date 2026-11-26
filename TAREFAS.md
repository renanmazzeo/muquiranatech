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
   Se a última entrada registrou um problema no site publicado, corrigi-lo é a tarefa desta execução.
2. Faça a **checagem de saúde**.
3. **Trabalhe em sequência, uma tarefa de cada vez, até acabar a fila ou a sua cota.** Para cada tarefa
   (a primeira `[~]` ou `[ ]` cujo pré-requisito esteja cumprido):
   1. **Teste antes de publicar** (ver "Publicar e testar no ar").
   2. Atualize o status aqui e acrescente o que fez na entrada desta execução no DIARIO.md.
   3. **Publique na `main` e teste no ar.** Só depois passe para a próxima tarefa.
   Tarefa grande? Publique cada parte que funcione sozinha e marque `[~]`, dizendo no DIARIO.md o que falta.
   A execução pode ser cortada a qualquer momento (cota esgotada): nada importante pode ficar só na sua cópia.
4. Tarefa esperando algo externo (uma coleta agendada, o dono)? Deixe `[~]`, anote o que falta e **siga para a
   próxima tarefa que não dependa disso**. Na execução seguinte, confira a pendente.
5. Só pare antes do fim da fila se: a próxima tarefa depende de algo que ainda não aconteceu (marque e diga o
   quê), ou algo no ar quebrou e você não conseguiu consertar nem reverter.

Status: `[ ]` a fazer · `[~]` em andamento · `[x]` feita, publicada e testada no ar · `[-]` impossível
(motivo no DIARIO.md).

## Regras (não negociáveis)
- **Publique direto na `main`** (é um protótipo; o dono quer ver tudo no portal). Mensagens de commit em
  português, explicando em linguagem simples o que muda para quem usa o site.
- **Nunca use `git push --force`** nem reescreva o histórico da `main`. Para desfazer algo, use `git revert`.
- **Nunca altere** `data/muquirana.db` nem `data.js`: são dos robôs de coleta. Se seu branch tocar neles, desfaça.
- **Nunca mexa** em credenciais ou segredos, no `coletar-pc.ps1` (use `docs/sondagens/` e o `"onde": "pc"` da watchlist), nem nas configurações da Cloudflare ou do
  GitHub (Pages, secrets, branch protection).
- **Nunca aumente** a frequência dos robôs: o plano grátis da Cloudflare tem 500 builds por mês.
- **Requisições às lojas:** no máximo 30 por tarefa, com 3 s ou mais entre elas.
- **Amazon: só pela rede do GitHub Actions**, nunca de outro lugar e nunca no PC do dono. O bloqueio da Amazon é
  por endereço de rede, então testes no GitHub não atrapalham a coleta que o PC do dono faz. No máximo 10
  requisições à Amazon por execução do agente.
- **Só serviços gratuitos.** Serviço pago, cadastro em site, aceitar termos, qualquer coisa em nome do dono:
  **não faça**. Anote no DIARIO.md em "Precisa do dono".
- Ficou em dúvida sobre o que o dono quer? Escolha a opção mais conservadora e deixe a pergunta em
  "Precisa do dono" no DIARIO.md.
- **Preço tem que ser igual ao da loja.** Toda loja nova precisa, antes de publicar, de uma conferência de 5 produtos:
  o preço que o coletor lê contra o preço que a página do produto mostra (à vista/Pix). Se não bater, não publique
  a loja: explique no DIARIO.md. Foi assim que pegamos o bug das ofertas da KaBuM! em 25/11.
- **Só vendedores confiáveis:** a própria loja ou lojas oficiais das marcas. Nada de marketplace genérico.
- Commits terminam com `Co-Authored-By: Claude <noreply@anthropic.com>`.

## Publicar e testar no ar
**Antes de publicar**
- Python: `python -m unittest` (depois da tarefa 1) e `ast.parse` em cada arquivo alterado. Coletor alterado:
  rode a coleta da loja numa cópia (`MUQ_DB=/tmp/teste.db`), nunca no banco real.
- Site: abra o `index.html` com o `data.js` atual no Chrome headless (se houver) a 1320 px e a 390 px, sem erro
  no console. Sem Chrome: ao menos carregue o `<script>` com `node` para pegar erro de sintaxe.
- Workflow alterado: confira o YAML com cuidado (um erro ali para a coleta).

**Publicar** (os robôs fazem commits na `main` várias vezes por dia)
```
git pull --rebase origin main      # conflito em data/ ou data.js: fique com a versão da main, nunca a sua
git push origin HEAD:main
```
Push recusado? `git pull --rebase` de novo e repita. Até 3 tentativas.

**Depois de publicar: testar no ar** (obrigatório)

O ambiente na nuvem **não consegue abrir** `muquiranatech.pages.dev` nem `github.io` (o proxy devolve 403), mas
consegue usar `api.github.com` sem login (repositório público, limite de 60 chamadas por hora). O teste no ar é
feito por ela. **Não use `sleep` longo** (é bloqueado): espere com um laço curto, por exemplo
`for i in $(seq 30); do <checagem> && break; sleep 10; done`.
- **A Cloudflare publicou?** Espere o check "Cloudflare Pages" do seu commit terminar e confira `success`:
  `curl -s https://api.github.com/repos/renanmazzeo/muquiranatech/commits/<sha>/check-runs` (campos `name`,
  `status`, `conclusion`). Um `failure` ali quer dizer que o site **não** foi atualizado.
- **O conteúdo publicado é o seu?** O site é cópia exata do commit. Confira no commit publicado
  (`https://api.github.com/repos/renanmazzeo/muquiranatech/contents/index.html?ref=<sha>`, conteúdo em base64)
  que a sua mudança está lá, e rode nele o teste do Chrome headless (ou `node`) de "Antes de publicar".
- **Os testes passaram?** Confira o check "testar" (workflow Testes) do seu commit, quando ele rodar.
- **Mexeu no coletor de uma loja?** Rodar a coleta aqui pode não provar nada (a rede da nuvem pode ser
  bloqueada pela loja, e a do GitHub Actions é outra). Para testar na rede do GitHub, use um workflow que rode
  no `push` (filtrado por `paths:`) e escreva o resultado como anotação (`echo "::notice::kabum 60 itens"`).
  Anotações são públicas: `GET /repos/.../check-runs/<id>/annotations`. Um teste sem produtos deve terminar em
  `failure`. Na execução seguinte, confira também a coleta agendada (checagem de saúde).
- Mexeu no workflow de coleta? Confira na checagem de saúde da próxima execução que a coleta agendada deu certo.
- **Algo quebrou no ar?** Corrija na hora. Se não conseguir em poucos minutos, `git revert` do seu commit,
  publique o revert, confira que o site voltou e registre no DIARIO.md o que aconteceu.
- Anote no DIARIO.md o resultado do teste no ar.

---

## Checagem de saúde (toda execução, poucos minutos)
- `data.js`: o campo `gerado` tem menos de 6 horas? Quantos produtos há de cada loja (prefixo do `id`)?
- `gh run list --workflow coletar.yml -L 5`: alguma execução terminou em `failure`? (`cancelled` feito à mão não
  é problema.) Se houver, leia o log com `gh run view <id> --log-failed`. Sem `gh` com login, o repositório é
  público: `curl -s "https://api.github.com/repos/renanmazzeo/muquiranatech/actions/workflows/coletar.yml/runs?per_page=5"`
  mostra `conclusion` e `html_url` de cada execução.
- Produtos `amazon:` sumiram? Então o robô do PC parou, e isso só o dono resolve: anote em "Precisa do dono".
- Anote os números na entrada do DIARIO.md. Se houver falha de coleta, corrigir vira a tarefa desta execução.

## Tarefas

### 1. [x] Testes automáticos dos leitores de loja
Por quê: sem testes, só descobrimos que uma loja mudou o formato quando o site mostra preço errado.
- Crie `tests/` com páginas salvas (fixtures pequenas, cortando o que não interessa) da KaBuM!, incluindo um
  produto **com oferta ativa** e um **sem oferta**. Para a Amazon, **não baixe nada**: monte um HTML mínimo
  com a estrutura que o `amazon.parse()` espera (resultado normal, patrocinado, preço riscado).
- Testes com `unittest` (sem dependências novas): a oferta da KaBuM! só vale dentro de `startsAt..endsAt`;
  `pick` respeita `must`, `not` e vendedores; `amazon.parse` ignora patrocinados; `mesclar` não duplica e não
  apaga a outra loja.
- Workflow `.github/workflows/testes.yml` rodando os testes a cada push na `main` que mude `collector/`,
  `tests/` ou `index.html` (use `paths:`, para não rodar a cada commit de preços dos robôs).
- Pronto quando: `python -m unittest` passa localmente e no GitHub.

### 2. [x] Steam (jogos de PC)
API pública, funciona do GitHub.
- `collector/steam.py` no mesmo formato do `kabum.py`: `store.steampowered.com/api/storesearch/?term=...&cc=br&l=portuguese`
  e, para o preço, `api/appdetails?appids=...&cc=br&filters=price_overview` (valores em centavos de real).
- Vendedor "Steam". Categoria `game`. Uma lista própria de cerca de 20 jogos populares de PC. Nas buscas que não
  fazem sentido para a Steam, use `{"skip": true}`.
- Inclua `steam` em `LOJAS` (`muq.py`), em `STORES` (`index.html`, cor `#1b2838`, domínio `store.steampowered.com`)
  e no `coletar.yml` (`--lojas kabum,steam`, mescla com `--lojas kabum,steam`).
- Pronto quando: a coleta local com `--lojas steam` traz cerca de 20 jogos, 5 conferidos batem com a Steam e,
  depois de publicar, uma coleta disparada no GitHub coloca os jogos da Steam no site.

### 3. [~] Mercado Livre (API oficial), deixar pronto para ligar
O dono ainda vai criar o app. O agente deixa tudo pronto para funcionar no dia em que os secrets existirem.
- `collector/mercadolivre.py`: token por `client_credentials` (`ML_CLIENT_ID` e `ML_CLIENT_SECRET` vindos de
  variáveis de ambiente) e busca em `api.mercadolibre.com/sites/MLB/search`. **Só lojas oficiais**
  (`official_store_id` preenchido) e itens novos. Preço: `price` do resultado.
- No `coletar.yml`, passe os secrets como variáveis de ambiente; sem eles, o coletor pula o Mercado Livre e
  escreve uma linha no log, sem falhar.
- Em `STORES` no site, a entrada `ml` já existe.
- Um guia curto em português (`docs/mercado-livre.md`): como o dono cria o app (developers.mercadolivre.com.br) e cadastra os dois
  secrets no GitHub (Settings → Secrets and variables → Actions).
- Pronto quando: os testes com uma resposta de exemplo da API passam e o workflow publicado roda sem erro sem
  os secrets.
  A tarefa fica `[x]` mesmo sem as credenciais; ligar de verdade fica em "Precisa do dono".

### 4. [-] Americanas (bloqueada para robôs em 26/11)
- A API VTEX pública responde: `americanas.com.br/api/catalog_system/pub/products/search?ft=...`.
- Problemas vistos em 25/11: a busca traz itens de outras categorias (pede-se "smart tv 55" e vem rack), e o preço
  à vista na página pode ser diferente do `Price` da API (desconto no Pix).
- Use só vendedor `AMERICANAS SA` com `AvailableQuantity > 0`, e `must`/`not` para tirar itens errados.
  Descubra de onde vem o preço à vista que a página mostra (outro campo da API, `Installments` com Pix, ou o
  HTML do produto) e confira 5 produtos.
- Se o preço não bater de jeito nenhum, marque `[-]` e explique no DIARIO.md.

### 5. [ ] Testar TODAS as lojas importantes (pedido do dono: todas devem aparecer no site)
O dono quer o máximo de lojas confiáveis no site, e **quer que você encontre um caminho que funcione: pelo GitHub
ou pelo PC dele. Sempre teste, e se não der, tente a próxima alternativa.** Só marque uma loja como impossível
depois de esgotar **todas** as combinações abaixo, nos **dois** lugares.

**Os dois lugares, e como testar em cada um** (ponte em `docs/sondagens/`, veja o LEIA-ME de lá):
- **GitHub:** escreva `docs/sondagens/pedido-github.json` com um `id` novo e publique. O workflow `sondar.yml`
  roda em ~3 min, com `requests` e com navegador de verdade (Playwright), e grava `resultado-github.json`.
  Leia com `git pull` (espere com laço curto).
- **PC do dono:** escreva `docs/sondagens/pedido-pc.json` com um `id` novo e publique. O robô do PC executa na
  próxima rodada (a cada 6h, só com o PC ligado) e grava `resultado-pc.json`. O PC tem IP residencial: muitas
  lojas que bloqueiam o GitHub (datacenter) liberam o PC. Enquanto espera, siga com outras lojas e tarefas.
- Já existe um **pedido inicial** nos dois lugares (Magalu, Casas Bahia, Pichau, Terabyte, Carrefour, Fast Shop,
  Kalunga, Mercado Livre e Amazon), em requests e navegador. Comece lendo esses resultados.

**Para cada loja, tente nesta ordem até uma funcionar, primeiro no GitHub e depois no PC:**
1. API pública da loja (muitas lojas brasileiras usam VTEX: `/api/catalog_system/pub/products/search?ft=...`;
   outras têm JSON embutido na página, como o `__NEXT_DATA__` da KaBuM!, ou uma API interna que a própria página
   chama: procure no HTML por URLs de API);
2. `requests` com cabeçalhos de navegador, outra URL de busca, a URL de categoria em vez da busca;
3. **Playwright com Chromium** (grátis), abrindo a página de busca como um navegador de verdade;
4. as mesmas três coisas **no PC do dono**.
Registre cada tentativa (lugar, jeito, resultado) na tabela do DIARIO.md.

**Onde a loja fica:** funcionou no GitHub → coleta no GitHub. Só funcionou no PC → marque `"onde": "pc"` na loja,
em `lojas` no `collector/watchlist.json` (o robô do PC passa a coletá-la sozinho; não precisa mexer no
`coletar-pc.ps1`). O PC só coleta com ele ligado, então prefira o GitHub quando os dois funcionarem.
Se a loja precisar de Playwright no PC, acrescente `playwright` ao `collector/requirements.txt` (o robô do PC
instala sozinho o que faltar).

Lojas para testar (registre o resultado de **todas** numa tabela no DIARIO.md e na tabela "Lojas" do CLAUDE.md):
- **Grandes varejistas:** Magazine Luiza, Casas Bahia, Ponto, Extra, Carrefour, Fast Shop, Americanas
  (se a tarefa 4 não resolveu), Shoptime, Submarino, Mercado Livre (página de busca, além da API da tarefa 3).
- **Lojas de informática e games:** Pichau, Terabyte, Kalunga, Girafa, Nuuvem, PlayStation Store,
  Nintendo eShop, Xbox Store.
- **Lojas oficiais de marcas:** Samsung, Apple, Dell, Lenovo, LG, Motorola.
- **Amazon pelo GitHub:** o `requests` recebe 503. Teste o **Playwright** com o mesmo filtro
  `rh=p_6:A1ZZFT5FULY4LN`. Se funcionar, a Amazon passa a ser coletada pelo GitHub também, sem depender do PC do
  dono: crie a tarefa para isso.

Para cada loja que funcionar (mostra produtos com preço): **crie uma tarefa nova aqui**, logo depois desta, no
padrão das tarefas 2 e 4 (coletor, vendedores confiáveis, conferência de 5 preços contra a página, inclusão no
`coletar.yml` e no `STORES` do site). Faça essas tarefas novas na sequência, **antes** da tarefa 6.
As que não funcionarem de jeito nenhum: registre o motivo (403, captcha, preço não confere) na tabela.
Nada de serviço pago de proxy ou de resolver captcha.

Playwright no GitHub Actions: `pip install playwright && python -m playwright install --with-deps chromium`.
Se uma loja só funcionar com Playwright, a coleta dela vai num **job separado** do `coletar.yml` (é mais lento), e
a mescla continua por loja (`mesclar --lojas <loja>`).

### 5b. [ ] Amazon aparecendo no site
- Na checagem de saúde, veja se há produtos `amazon:` no `data.js`. Se não houver há mais de 12 horas, o robô do
  PC do dono não está conseguindo coletar: anote em "Precisa do dono" (o log fica em
  `%LOCALAPPDATA%\MuquiranaTech\coleta.log` no PC dele).
- O teste `amazon-coletor` no `resultado-pc.json` diz se o PC do dono está conseguindo coletar a Amazon. Se o PC
  estiver bloqueado (503), tente reduzir o ritmo (`pausa` maior na watchlist) ou outra URL de busca, e peça um
  teste novo ao PC.
- Se o teste da tarefa 5 mostrou que a Amazon funciona com Playwright no GitHub, implemente a coleta da Amazon
  no GitHub (job separado, mesmo filtro de vendedor e as mesmas buscas/ajustes da watchlist) e confira 5 preços.
  Assim a Amazon aparece no site mesmo com o PC do dono desligado.
- Pronta quando: há produtos `amazon:` no `data.js` publicado, vindos do PC ou do GitHub.

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
- Corrija a watchlist com `must`/`not` a partir da lista. **Não remova buscas inteiras** sem explicar no DIARIO.md.
- Pronto quando: o script roda e o DIARIO.md traz o que foi encontrado e o que foi ajustado.

### 9. [ ] Tarefa final: revisão geral e encerramento
Só quando todas as tarefas acima estiverem `[x]` ou `[-]`.
- Abra o site no Chrome headless a 390 px e a 1320 px, com os dados atuais, e confira: todas as lojas ativas
  aparecem, ficha do produto, Black Fraude, filtros, "Mostrar mais" e "Como funciona". Faça isso no site
  publicado (https://muquiranatech.pages.dev).
- Atualize o README.md (o que é, lojas, como rodar) e o CLAUDE.md (arquitetura e tabela de lojas).
- No DIARIO.md: um resumo final do que ficou pronto, do que ficou impossível e do que depende do dono, e
  `ESTADO: CONCLUÍDO`.
- Em "Precisa do dono" no DIARIO.md: desligar o agendamento em https://claude.ai/code/routines.

## Fora do escopo do agente
Ficam para o dono, ou para uma conversa com o Claude depois:
- revisar as regras da Black Fraude com dados reais (precisa de mais de 35 dias de histórico);
- retestar lojas bloqueadas no futuro;
- domínio próprio, Programa de Associados da Amazon, alertas de preço.
