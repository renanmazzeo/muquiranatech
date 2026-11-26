# Diário do MuquiranaTech

Registro de tudo o que foi feito, do mais recente para o mais antigo. O agente autônomo acrescenta uma entrada
por execução (modelo no fim do arquivo) e lê as 3 últimas antes de começar.

## Precisa do dono
Pendências que só o dono resolve. O agente acrescenta itens aqui e o dono apaga quando resolver.
- [ ] Mercado Livre: criar o app e guardar as credenciais como secrets do GitHub (ver TAREFAS.md).
- [ ] Cloudflare: desligar os builds de prévia de branches, para os PRs do agente não gastarem o limite grátis.
- [ ] Amazon: o robô do PC foi instalado em 25/11, mas a Amazon estava bloqueando este PC por excesso de testes.
      Conferir no `%LOCALAPPDATA%\MuquiranaTech\coleta.log` se as coletas seguintes deram certo.
- [ ] Opcional: Programa de Associados da Amazon; domínio próprio.

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
- Agente autônomo na nuvem trabalhando pela fila do TAREFAS.md, sempre por pull request.

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
