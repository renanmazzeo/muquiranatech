# Diário do MuquiranaTech

Registro de tudo o que foi feito, do mais recente para o mais antigo. O agente autônomo acrescenta uma entrada
por execução (modelo no fim do arquivo) e lê as 3 últimas antes de começar.

ESTADO: EM ANDAMENTO
<!-- O agente troca para "ESTADO: CONCLUÍDO" na tarefa final do TAREFAS.md. Depois disso, ele não faz mais nada. -->
<!-- Entradas novas: logo depois do "---" que fecha a seção "Precisa do dono", antes da entrada mais recente. -->


## Precisa do dono
Pendências que só o dono resolve. O agente acrescenta itens aqui e o dono apaga quando resolver.
- [ ] Mercado Livre: criar o app e guardar as credenciais como secrets do GitHub (ver TAREFAS.md).
- [ ] Amazon: o robô do PC foi instalado em 25/11, mas a Amazon estava bloqueando este PC por excesso de testes.
      Conferir no `%LOCALAPPDATA%\MuquiranaTech\coleta.log` se as coletas seguintes deram certo.
- [ ] Opcional: Programa de Associados da Amazon; domínio próprio.

---

## 2026-11-26 02:00 UTC · agente · tarefa 2 (Steam), parte 1
**Saúde:** data.js gerado às 00:50 UTC · 303 produtos KaBuM! · 0 Amazon (segue pendente com o dono) · coletas: última `success` às 23:50 UTC de 25/11, as 3 seguintes `cancelled` (à mão) e uma em andamento.
**Feito:** criado `collector/steam.py` (busca pela API pública da Steam, preço final em reais, vendedor "Steam"), lista própria de 21 jogos populares na watchlist (`lojas.steam.buscas`; o coletor usa a lista da loja quando ela existe), `steam` em `LOJAS`, em `STORES` do site e no `coletar.yml` (coleta e mescla `kabum,steam`). 3 testes novos (17 no total, todos ok). Novo workflow `testar-steam.yml`: roda no push, coleta numa cópia do banco e confere 5 preços contra a API de detalhes, com o resultado nas anotações.
**Como testei:** `python -m unittest` ok; coleta simulada de ponta a ponta numa cópia do banco com resposta de exemplo; YAML e JS do site conferidos. Esta nuvem não alcança a Steam (proxy 403), por isso a conferência real é a do workflow no GitHub.
**Teste no ar:** commit 8132864: check "Cloudflare Pages" `success`, Testes `success`. `testar-steam.yml` `success` na rede do GitHub: 21 jogos coletados e 5 conferidos contra a API de detalhes, todos iguais (RDR2 R$ 74,97; Hades II R$ 62,29; Cyberpunk R$ 199,90; Baldur's Gate 3 R$ 139,99; Terraria R$ 32,99).
**Falta:** disparei uma coleta (workflow_dispatch às 01:33 UTC), mas ela está na fila atrás da coleta de histórico de 4 meses (iniciada 00:51, até 270 min; o grupo `coleta` não roda duas ao mesmo tempo). Na próxima execução: conferir se `data.js` já tem produtos `steam:` (esperado ~21) e então marcar `[x]`.
**Precisa do dono:** nada novo.

---

## 2026-11-26 01:40 UTC · sessão com o dono · ajustes no roteiro do agente
**Feito**
- Tarefa 1 conferida e marcada `[x]`: o workflow Testes passou no GitHub (run 45735492909), e o check
  "Cloudflare Pages" do commit cc30b58 deu `success`.
- Roteiro mudado a pedido do dono: o agente faz **várias tarefas por execução**, uma de cada vez, até acabar a
  fila ou a cota, em vez de parar depois de uma.
- "Teste no ar" refeito para funcionar na nuvem: a nuvem não abre pages.dev nem github.io, então o teste usa a API
  pública do GitHub (check "Cloudflare Pages" do commit, conteúdo do commit publicado, anotações de workflow).
- Sem `sleep` longo: espera com laço curto.
- Agendamento a cada 2h (antes 6h).

---

## 2026-11-26 01:30 UTC · agente · tarefa 1 (testes dos leitores de loja)
**Saúde:** data.js gerado às 00:50 UTC (ok, menos de 6 h) · 303 produtos KaBuM! · 0 Amazon (o robô do PC ainda não publicou nada: ver "Precisa do dono") · coletas: última `success` às 23:50 UTC; as 3 seguintes `cancelled` (provavelmente à mão) e uma em andamento.
**Feito:** criada a pasta `tests/` com 14 testes (`python -m unittest`): oferta da KaBuM! só vale dentro de `startsAt..endsAt`, caixa aberta é ignorada, `pick` respeita vendedor, `must`, `not` e limite, `amazon.parse` ignora patrocinados e lê o preço riscado, e `mesclar` não duplica nem apaga a outra loja. Criado o workflow `testes.yml` (roda só quando mudam `collector/`, `tests/` ou `index.html`). As páginas de teste (fixtures) são pequenas e montadas à mão no formato real (`__NEXT_DATA__`), sem baixar nada das lojas.
**Como testei:** `python -m unittest` local: 14 testes ok. Falta ver o workflow passar no GitHub, por isso a tarefa 1 fica `[~]`.
**Teste no ar:** não consegui: o proxy desta nuvem bloqueia (403) muquiranatech.pages.dev e github.io. Esta mudança não toca o site (só testes e workflow), então o risco é baixo. O workflow `testes.yml` estava `queued` quando terminei.
**Próximo passo:** na próxima execução, conferir se `testes.yml` passou no GitHub; se sim, marcar tarefa 1 como `[x]`.
**Precisa do dono:** nada novo.

---

## 2026-11-25 (noite) · sessão com o dono · montagem do projeto
**Feito**
- Repositório público `renanmazzeo/muquiranatech` criado. Site no GitHub Pages e depois na Cloudflare Pages
  (https://muquiranatech.pages.dev).
- Seção **Black Fraude × Black Firmeza**: compara o preço da promoção com o preço normal (mediana de 31 a 90 dias
  atrás). Botão no topo, listas, selos nos cards e filtros.
- **Muquirômetro** virou um termômetro colorido, sem nota nem descrição (pedido do dono).
- **Celular:** busca numa linha própria, números do topo em grade 2x2, ficha do produto como gaveta, botão de
  fechar sempre visível e o "voltar" do celular fechando a ficha.
- **Ficha do produto:** preço atual em destaque (com centavos, "à vista no Pix"), hora em que o preço foi visto,
  fim da oferta e botão da loja verde e chamativo.
- **Catálogo:** de 25 para 112 buscas, com 5 categorias novas (Gabinetes e coolers, Tablets e e-readers,
  Smartwatches, Redes e energia, Casa inteligente). Cerca de 300 produtos da KaBuM! e 274 da Amazon.
- **Bug de preço corrigido:** na Black Friday a KaBuM! guarda o preço promocional em `offer`, e o coletor lia o
  preço sem oferta (um notebook aparecia por R$ 9.999 e estava R$ 7.099). Conferidos 15 produtos sorteados:
  todos iguais aos da loja.
- **Amazon:** coletor com filtro "vendido e entregue pela Amazon.com.br". Ela bloqueia o GitHub (503), então é
  coletada pelo PC do dono (tarefa do Windows a cada 6h, numa cópia própria do repositório).
- **Robôs sem conflito:** cada robô coleta numa cópia do banco e mescla só as linhas da sua loja antes do push.
- Histórico da Wayback limitado a 12 meses (padrão), mais recentes primeiro, com limite de tempo.
- Coleta da KaBuM! a cada 3h. Data do dia no fuso de Brasília.

**Decisões do dono**
- Só serviços gratuitos. Netlify descartada (limite de deploys); Cloudflare Pages escolhida.
- Histórico de no máximo 1 ano; nesta primeira vez, 4 meses.
- Ter todas as lojas possíveis, mesmo sem histórico: o histórico se forma a partir de agora.
- Amazon coletada pelo PC do dono. Mercado Livre: o dono vai criar o app (pendente).
- Agente autônomo na nuvem trabalhando pela fila do TAREFAS.md, publicando direto na main e testando o site no ar depois de cada publicação. O agente termina quando a fila acaba (ESTADO: CONCLUÍDO).

**Lojas testadas** (25/11/2026): ver a tabela no CLAUDE.md.

**Em andamento**
- Execução do GitHub com histórico de 4 meses da Wayback (iniciada às 21h51 BRT de 25/11).

---

## Modelo de entrada (copie e preencha)
```
## AAAA-MM-DD HH:MM · agente · <tarefa>
**Saúde (tarefa 0):** data.js gerado às HH:MM · X produtos KaBuM! · Y Amazon · últimas coletas: ok/falha
**Feito:** o que mudou, em linguagem simples
**PR:** link
**Como testei:** ...
**Próximo passo:** ...
**Precisa do dono:** (se houver, copie também para a seção lá em cima)
```
