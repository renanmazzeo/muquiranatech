# Diário do MuquiranaTech

Registro de tudo o que foi feito, do mais recente para o mais antigo. O agente autônomo acrescenta uma entrada
por execução (modelo no fim do arquivo) e lê as 3 últimas antes de começar.

ESTADO: EM ANDAMENTO
<!-- O agente troca para "ESTADO: CONCLUÍDO" na tarefa final do TAREFAS.md. Depois disso, ele não faz mais nada. -->
<!-- Entradas novas: logo depois do "---" que fecha a seção "Precisa do dono", antes da entrada mais recente. -->


## Precisa do dono
Pendências que só o dono resolve. O agente acrescenta itens aqui e o dono apaga quando resolver.
- [ ] Mercado Livre: "Criar nova aplicação" está desabilitado na conta do dono (26/11). Se liberar (ou o suporte do ML responder), criar o app, guardar ML_CLIENT_ID/ML_CLIENT_SECRET nos secrets e rodar o workflow "Testar Mercado Livre". Agente: não insista no ML até lá.

- [ ] Tarefa 5 (navegador Playwright nas lojas que bloqueiam robôs): o sistema de permissões da execução automática recusou criar o teste, por ser tentativa de passar por bloqueio anti-robô. Diga se autoriza (ou marque a tarefa `[-]` e atualize a tabela "Lojas").
- [ ] Opcional: Programa de Associados da Amazon (depois do domínio no ar).

---

## 2026-11-26 18:40 UTC · agente · tarefa 5d (Xbox Store)
**Saúde:** data.js gerado às 16:46 UTC · 4.190 KaBuM! · 286 Amazon · 153 Samsung · 65 Kalunga · 32 Motorola (já no ar) · 21 Steam · 20 PlayStation · últimas execuções do GitHub `success`.
**Feito:** `collector/xbox.py` (navegador; lê nome, preço e "preço original" do `aria-label` dos cartões da busca; ignora jogo sem preço), 20 jogos na watchlist (`lojas.xbox`, **com `"onde": "teste"`: ainda NÃO é coletada pelos robôs**), loja em `STORES` do site, 2 testes novos (36 no total, ok) e workflow `testar-xbox.yml` (coleta numa cópia e confere 5 fichas na rede do GitHub).
**Teste no ar:** commit 47480eb: Cloudflare Pages `success`, Testes `success`. `testar-xbox` **falhou**: 0 jogos nas 20 buscas na rede do GitHub (o cartão com `a[href*="/games/store/"]` não apareceu em 30 s; a página real difere da guardada ou a Microsoft limitou o robô). A loja segue com `"onde": "teste"`, então nada errado foi ao ar.
**Próximo passo:** workflow de diagnóstico que guarde o HTML/captura da busca `forza` em `docs/sondagens/html/` para ajustar o seletor; se não resolver, Xbox `[-]`.
**Falta:** ver o `testar-xbox` passar com 5 preços iguais; só então trocar `"onde"` para `"github-nav"` (entra no job `coletar-navegador`). Lenovo: HTML guardado é grande e misturado (kits, preço "de" e preço atual em blocos diferentes), ainda sem coletor.
**Precisa do dono:** nada novo.

---

## 2026-11-26 16:30 UTC · agente · saúde e tarefa 8 (revisar.py)
**Saúde:** data.js gerado às 14:26 UTC (2 h) · 4.173 KaBuM! · 286 Amazon · 64 Kalunga · 20 PlayStation · 150 Samsung · 21 Steam · 0 Motorola (a coleta de 14:09 é anterior à loja) · nenhuma coleta `schedule` desde 25/11 (só `workflow_dispatch`, todas `success`). Disparei uma coleta à mão (16:3x UTC) para trazer `motorola:`.
**Feito:** `collector/revisar.py` (só leitura; lê data.js e lista preço fora de 25%–400% da mediana da categoria e acessório em categoria de aparelho). Resultado: 1.097 suspeitos, quase todos falsos alarmes (a mediana da categoria mistura produtos de faixas muito diferentes: TV 98" × TV box, monitor OLED × monitor comum, jogos de R$ 12 × R$ 300). Achados reais: Amazon traz carregadores/power banks e controles na categoria `celular`/`console` (acessórios de 9 itens na Amazon e 19 na KaBuM!). Não removi buscas nem mexi na watchlist: o dono aceita acessórios das lojas, e a categoria aproximada não engana o preço. Sugestão futura: comparar preço só entre produtos da mesma busca, não da categoria inteira.
**Teste no ar:** só script novo e documentos; site não mudou (sem teste de Cloudflare necessário).
**Próximo passo:** conferir `motorola:`; Lenovo e Xbox (navegador) na 5d; depois tarefa final (9) quando a 5d fechar.
**Precisa do dono:** nada novo.

---

## 2026-11-26 15:40 UTC · dono + Claude · Samsung, comparação entre lojas, "Como funciona", domínio
**Feito:** Samsung no ar (150 produtos, catálogo VTEX, preço do Pix); Apple deixada de lado. Comparação "o mesmo
produto em outras lojas" (37 grupos conferidos um a um; regras contra DDR4×DDR5, 5060×5070, 50"×55"). Contagem e
logo no filtro de lojas. `como-funciona.html`, `privacidade.html`, `og.png`, `favicon.svg`, meta tags, `LICENSE`.
**Domínio:** muquiranatech.com.br registrado (vence 26/11/2027), nameservers do Cloudflare em transição no registro.br.
Falta: ligar o domínio no Pages (Custom domains), Email Routing `contato@`, trocar `og:image` para o domínio novo.
**Mercado Livre:** dono pediu acesso à API; aguardando resposta.

## 2026-11-26 15:00 UTC · agente · tarefa 5d (Motorola)
**Saúde:** data.js gerado às 14:26 UTC · 4.173 KaBuM! · 286 Amazon · 64 Kalunga · 20 PlayStation · 150 Samsung · 21 Steam · coletas do GitHub `success` (todas disparadas à mão; segue sem `schedule`).
**Feito:** `collector/motorola.py` (API VTEX pública, categoria Smartphones, preço do Pix, só vendedor Motorola), loja na watchlist, em `muq.py` e em `STORES` do site, 2 testes novos (34 no total, ok), workflow `testar-motorola.yml`. A sonda temporária mostrou na rede do GitHub que a API responde e que só há "Smartphones", "Acessórios" (misturado, deixei de fora) e "Seguros".
**Conferência (rede do GitHub):** 32 produtos; 5 preços iguais aos da ficha (Moto g Max 5G R$ 2.499; g47 R$ 1.499; Edge 70 R$ 3.149,10; g06 256GB R$ 1.079; g35 R$ 899,10).
**Teste no ar:** commit e2d4003: Cloudflare Pages `success`, Testes `success`, `testar-motorola` `success`. Falta ver `motorola:` no data.js após a próxima coleta.
**Próximo passo:** conferir `motorola:`; Lenovo e Xbox (navegador); depois tarefas 6, 7, 8.
**Precisa do dono:** nada novo.

---

## 2026-11-26 14:00 UTC · dono + Claude · filtros e preços desatualizados
**Problemas que o dono viu:** "Só Black Fraude" mostrava cartões "Até o Muquirana compra"; alguns preços diferentes da loja.
**Feito:** selos coerentes com o termômetro (Fraude só acima de 10% do menor; Firmeza só até 10%); aviso amarelo
para "de" inflado em preço bom; ofertas vencidas somem do site; `exportar` ignora preço com mais de 36 h; `data.js?v=`
contra cache; removida a hora da última atualização do topo e do rodapé (pedido do dono).
**Conferência:** teste no navegador: Fraude = 10 "Segura a carteira" + 13 "Cilada!"; Firmeza = só Compra/Aprova;
200 ofertas vencidas às 10h escondidas; sem erros no console. Testes unitários ok.

## 2026-11-26 13:30 UTC · agente · tarefa 5d (PlayStation Store)
**Saúde:** data.js gerado às 12:00 UTC · 4.152 KaBuM! · 286 Amazon · 64 Kalunga · 21 Steam · coletas do GitHub `success` (as últimas foram disparadas à mão; segue sem `schedule`).
**Feito:** `collector/playstation.py` (lê nome, id e preço dos cartões da busca com navegador; ignora preço só para assinantes), 20 jogos na watchlist (loja `"onde": "github-nav"`), loja em `STORES` do site, 2 testes novos (30 no total, ok), workflow `testar-playstation.yml` e job separado `coletar-navegador` no `coletar.yml` (Playwright; mescla só `playstation`).
**Conferência:** na rede do GitHub, 5 jogos conferidos contra a ficha do produto, todos iguais (Tsushima Diretor R$ 299,90; BG3 R$ 299,90; GTA V R$ 198,90; Elden Ring R$ 299,90; CoD R$ 297,41). Primeira rodada achou DLCs (Elden Ring Shadow of the Erdtree, Tsushima Legends): filtrados com `not`.
**Teste no ar:** commit 290354c: Cloudflare Pages `success`, Testes `success`, `testar-playstation` `success`. Falta ver `playstation:` no data.js após a coleta.
**Próximo passo:** conferir `playstation:` no data.js; depois Lenovo/Xbox/Motorola/Apple/Samsung.
**Precisa do dono:** nada novo.

---

## 2026-11-26 12:30 UTC · dono (sessão local) · catálogo da KaBuM!, busca inteligente
**Feito:** coleta por **catálogo** da KaBuM! (13 categorias de tecnologia inteiras, só "Vendido pela KaBuM!", `kabum.catalogo`): cerca de 4.150 produtos da KaBuM! em vez de 320; categoria do site pelo nome (`collector/categorias.py`, com teste). Amazon com `max_busca: 8` (mesmo número de acessos, mais produtos por busca) e 12 buscas novas de modelos populares mais antigos (RTX 3060/4060, Ryzen 5 5500...). Tabela `prices` reordenada por dia (o .db pesa menos no git). Site: busca inteligente (tolera erro de digitação, "rtx3060", sinônimos), painel de resultados embaixo da busca e grade de 60 em 60. Conferi 10 preços do catálogo contra a página do produto: todos iguais.
**Para o agente:** a KaBuM! agora tem milhares de produtos sem histórico ("Muquirana de olho" por 30 dias). Ao mexer na watchlist ou no `muq.py`, manter `catalogo`, `max_busca` e a ordem da tabela `prices`.

---

## 2026-11-26 11:00 UTC · dono (sessão local) · lojas novas visíveis e agendamento
**Feito:** a ordem "melhores" do site agora intercala as lojas; antes, Amazon e Kalunga (sem histórico) ficavam todas no fim da lista e pareciam não existir. Agendamento da coleta movido para o minuto 17 (no minuto 0 o GitHub não disparava nenhuma rodada `schedule`). Amazon pelo PC confirmada (286 produtos). Pendências resolvidas removidas de "Precisa do dono".

---

## 2026-11-26 10:30 UTC · agente · saúde, 5c fechada, PlayStation avaliada
**Saúde:** data.js gerado às 08:39 UTC (cerca de 2 h) · 323 KaBuM! · 286 Amazon · 21 Steam · 57 Kalunga · coletas `success` (a de 08:28 UTC foi disparada à mão; segue sem aparecer coleta `schedule`: dono conferir o cron).
**5c:** `[x]`. `kalunga:` está no data.js publicado (57 produtos) e o check "Cloudflare Pages" do commit ed8f9e4 deu `success`.
**5d:** o HTML guardado da PlayStation Store traz nome, id e preço (`R$114,90` etc.) em `data-telemetry-meta` de cada cartão (`product-tile`), então dá para ler sem API; falta o coletor (job com Playwright), a conferência de 5 preços e a inclusão no `coletar.yml`. Nada publicado no site nesta execução (só TAREFAS e DIARIO).
**Próximo passo:** coletor da PlayStation a partir de `docs/sondagens/html/playstation-html.html`, depois Lenovo/Xbox/Motorola/Apple.
**Precisa do dono:** nada novo.

---

## 2026-11-26 08:40 UTC · agente · saúde, coleta e 5d (sondagem html5)
**Saúde:** data.js gerado às 04:35 UTC (4 h) · 308 KaBuM! · 286 Amazon · 21 Steam · 0 Kalunga · **a coleta agendada de 3 h não está disparando** (última `schedule` não existe; só `workflow_dispatch`; a última foi 01:33 UTC). O cron do GitHub é pouco confiável, mas vale o dono conferir em Actions se o workflow não está desativado.
**Feito:** disparei uma coleta (08:28 UTC, `in_progress` ao escrever) para trazer `kalunga:` ao site. Sondagem `html5` no GitHub (navegador, HTML guardado em `docs/sondagens/html/`): Apple (43 preços na página), Lenovo (100), Motorola (15), PlayStation (61), Xbox (36): todas 200, sem bloqueio. Falta montar cada coletor (um por loja, em job com Playwright) e conferir 5 preços contra a ficha; nada publicado no site nesta execução.
**Próximo passo:** conferir `kalunga:` no data.js (5c → `[x]`); começar o coletor da PlayStation Store ou Lenovo a partir do HTML guardado.
**Precisa do dono:** conferir se o agendamento (cron) do workflow "Coletar preços" está ativo em Actions.

---

## 2026-11-26 06:30 UTC · agente · saúde, 5c e 5d (leitura do HTML guardado)
**Saúde:** data.js gerado às 04:35 UTC (cerca de 2 h) · 308 KaBuM! · 286 Amazon · 21 Steam · 0 Kalunga · última coleta do GitHub `success` às 01:33 UTC (nenhuma coleta agendada nova apareceu desde então; conferir na próxima execução se o agendamento de 3 h está disparando).
**5c:** segue `[~]`: ainda sem `kalunga:` no data.js, porque a coleta com a Kalunga ainda não rodou.
**5d:** li o HTML guardado. Dell: o arquivo guardado é "Access Denied" (Akamai), então o "ok" da rodada 2 era instável e não há como montar coletor confiável (Dell fica `[-]` por ora, retestar depois). Samsung: o HTML tem 400 KB mas **nenhum preço** (carrega por JavaScript), então precisa de navegador e de achar a API interna; fica para a próxima execução. Apple, Lenovo, Motorola, PlayStation, Xbox: ainda não tentados. Nada publicado no site nesta execução.
**Próximo passo:** conferir `kalunga:` no data.js; pedir sondagem nova com `guardar` para Apple/Lenovo/Motorola/PlayStation/Xbox e procurar APIs internas.
**Precisa do dono:** nada novo.

---

## 2026-11-26 06:00 UTC · agente · tarefa 5c (Kalunga)
**Feito:** `collector/kalunga.py` (HTML da busca; a lista nem sempre traz o preço à vista, então `refinar()` confere cada item na ficha do produto, que é o que o cliente vê), 20 buscas próprias na watchlist, loja `kalunga` em `STORES`, 4 testes novos (26 no total, ok). Fichas de 8 produtos guardadas pela sondagem: o preço lido bate com o cabeçalho da ficha nas 8. Workflow `testar-kalunga.yml` no GitHub: 57 produtos, 5 conferidos, todos OK (a lista dava, por ex., R$ 2.781,60 num notebook cuja ficha mostra R$ 2.693,76: por isso a conferência na ficha). Só depois disso a loja entrou na coleta agendada.
**Teste no ar:** falta ver `kalunga:` no data.js depois da próxima coleta (tarefa 5c segue `[~]`).
**Próximo passo:** conferir a coleta; depois 5d (Dell, Samsung, Apple, Lenovo, Motorola, PlayStation, Xbox) e Carrefour no PC (`"onde": "pc"` precisa de coletor).

---

## 2026-11-26 04:50 UTC · agente · tarefa 5 (sondagem das lojas) e 5b
**Saúde:** data.js gerado às 02:47 UTC · 308 KaBuM! · 286 Amazon (do PC) · 21 Steam · coletas do GitHub `success`.
**5b:** há 286 produtos `amazon:` no data.js publicado, então a tarefa 5b está `[x]` (vindo do PC). Teste `amazon-coletor` no PC: ok. Amazon por navegador no GitHub: "Algo deu errado", segue só pelo PC.
**Sondagem, rodadas 1 e 2** (`funcionou` = 200, sem bloqueio e com preços na página; ainda **não** é loja publicada, falta coletor e conferência de 5 preços):
| Loja | GitHub | PC |
|---|---|---|
| Magalu, Casas Bahia | 403 (requests e navegador) | 403 |
| Pichau | 403 / manutenção | navegador ok, mas com preços R$ 0,00 e R$ 200.000 na página |
| Terabyte | 403 Cloudflare | navegador 200, mas com bloqueio detectado |
| Carrefour | 403 "Acesso Bloqueado" | **ok** (requests e navegador) |
| Kalunga | **ok** (requests) | ok |
| Fast Shop | 404 (URL errada, testar outra) | 404 |
| Mercado Livre (busca) | sem preços (só pela API) | igual |
| Amazon | navegador: erro | coletor ok |
| Submarino, Girafa | domínio não resolve | pendente |
| Nuuvem, LG | 403 | pendente |
| Samsung | **ok** (navegador) | pendente |
| Apple | **ok** | pendente |
| Dell | **ok** só com requests | pendente |
| Lenovo | **ok** só com navegador | pendente |
| Motorola, PlayStation Store, Xbox | **ok** (navegador) | pendente |
**Feito:** `sondar.py` agora guarda o HTML (`"guardar": true`, em `docs/sondagens/html/`) para montar os coletores. Pedido `html1` (Kalunga, Dell, Samsung) no GitHub. Criadas as tarefas 5c (Kalunga) e 5d (marcas e jogos) no TAREFAS.md.
**Próximo passo:** ler o HTML guardado e fazer o coletor da Kalunga; ler a rodada 2 do PC (Carrefour → `"onde": "pc"`).
**Precisa do dono:** nada novo. (O item da tarefa 5 sobre Playwright, lá em cima, parece resolvido pela ponte de sondagens; deixei para o dono apagar.)

---

## 2026-11-26 03:10 UTC · agente · tarefa 5 travada
Tentei criar o workflow `testar-navegador.yml` (Chromium abrindo uma busca de Magalu, Casas Bahia, Pichau, Terabyte e Carrefour). A permissão foi negada pelo classificador da execução automática (acesso a lojas que bloqueiam robôs). Não contornei: nada foi criado. Pendência em "Precisa do dono". As tarefas 6, 7 e 8 não dependem dela e ficam para as próximas execuções.

---

## 2026-11-26 03:00 UTC · agente · tarefa 4 (Americanas) impossível
**Feito:** criei `testar-americanas.yml` (sonda sem salvar nada, 6 buscas com 3 s entre elas) e rodei na rede do GitHub, duas versões (com e sem `_from/_to`). Todas as buscas à API VTEX devolveram **HTTP 400 "Bad Request! Scripts are not allowed!"** (bloqueio do firewall da loja contra robôs). Sem acesso à API, não dá para conferir 5 preços; tarefa 4 marcada `[-]` e tabela "Lojas" do CLAUDE.md atualizada. Não tentei contornar o bloqueio.
**Teste no ar:** commits só mexem em workflow/documentação; Cloudflare Pages `success`.
**Tarefa 3:** segue `[~]`, aguardando a coleta agendada das 03:00 UTC (primeira com o Mercado Livre sem secrets).
**Precisa do dono:** nada novo.

---

## 2026-11-26 02:30 UTC · agente · tarefa 2 (Steam) fechada; tarefa 3 aguardando coleta
**Saúde:** data.js gerado às 02:21 UTC · 308 produtos KaBuM! · 21 Steam · 0 Amazon (pendente com o dono) · coleta disparada às 01:33 terminou `success`.
**Feito:** conferi que `data.js` na `main` já tem os 21 jogos `steam:` (coleta no GitHub 45736524930 deu `success` e o commit de preços foi publicado; Cloudflare Pages `success`). Tarefa 2 marcada `[x]`.
**Tarefa 3:** a coleta acima rodou com o workflow antigo (commit 8132864, sem o Mercado Livre). A primeira coleta com o ML sem secrets é a agendada das 03:00 UTC; conferir na próxima execução (tarefa 3 segue `[~]`).

---

## 2026-11-26 02:30 UTC · agente · tarefa 3 (Mercado Livre), parte 1
**Feito:** `collector/mercadolivre.py` (token `client_credentials`, busca na API oficial só com `official_store=all` e itens novos, exige `official_store_id`), loja `ml` na watchlist (vendedor "Loja oficial", usa as mesmas 112 buscas), `coletar.yml` passa os secrets `ML_CLIENT_ID`/`ML_CLIENT_SECRET` e coleta `kabum,steam,ml`; sem os secrets o coletor escreve "pulando" e segue sem falhar. Guia `docs/mercado-livre.md`. 5 testes novos com resposta de exemplo (22 no total, todos ok). Coleta local `--lojas ml` sem credenciais: pulou sem erro.
**Falta para `[x]`:** ver a coleta agendada/disparada rodar no GitHub sem erro e sem os secrets (a fila de coletas está ocupada pelo histórico de 4 meses; ver tarefa 2). Ligar de verdade depende do dono (secrets).
**Precisa do dono:** criar o app e os 2 secrets (guia em `docs/mercado-livre.md`; já listado acima).

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

### 26/11/2026 — Domínio próprio no ar (conversa com o dono)
- `muquiranatech.com.br` registrado no registro.br e com DNS no Cloudflare (servidores trocados às 14h03).
- No Cloudflare Pages, domínios personalizados `muquiranatech.com.br` e `www.muquiranatech.com.br` → `muquiranatech.pages.dev`. Os dois respondem 200.
- Prévia do WhatsApp (`og:image`) e CLAUDE.md passam a usar o domínio novo.
- Registros de e-mail atuais (MX ".", SPF `-all`, DMARC reject) bloqueiam e-mails falsos em nome do domínio; trocar só ao ativar o Email Routing.
- E-mail `contato@muquiranatech.com.br` ativo (Cloudflare Email Routing → Gmail do projeto; teste do dono chegou). LICENSE e privacidade.html passam a usar esse endereço.
- Lenovo no site: `collector/lenovo.py` (lista pela API das categorias, preço do Pix pela API da ficha; 10 de 10 preços iguais à ficha; 175 produtos também pelo GitHub). Lomadee e Instagram: ver CLAUDE.md e `marca/instagram.py`.
