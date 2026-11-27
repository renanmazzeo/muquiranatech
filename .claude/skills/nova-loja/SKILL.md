---
name: nova-loja
description: Roteiro para colocar uma loja nova (ou ampliar uma loja) no MuquiranaTech com preço confiável. Use quando o dono pedir "coloca a loja X", "aumenta os produtos da loja Y", "a loja Z aprovou / liberou a API" ou digitar /nova-loja.
---

# Nova loja no MuquiranaTech

Objetivo: a loja aparece no site com **o mesmo preço que a loja mostra** (à vista / Pix), só de vendedor confiável,
sem burlar nenhuma proteção e sem quebrar o site no ar (todo push na `main` publica na hora).
Fale com o dono em português simples. Antes de tudo: `git pull`.

## 1. Escolher a fonte (nesta ordem de preferência)
1. **API ou feed oficial** de afiliado (Awin, Lomadee, AliExpress, Shopee, Mercado Livre). Chaves só como secret do
   GitHub, digitadas pelo dono com `gh secret set NOME -R renanmazzeo/muquiranatech`. Nunca peça a chave no chat,
   nunca grave chave em arquivo do repositório.
2. **API pública que a própria loja usa** (ex.: VTEX `api/catalog_system/pub`, como Samsung e Motorola; a de
   categoria + a de preço da ficha, como Lenovo; `appdetails`, como Steam).
3. **Página pública com navegador** (Playwright), como Xbox e PlayStation: só páginas permitidas.

## 2. Regras que não se quebram
- Leia o `robots.txt` primeiro. Caminho proibido (ex.: `/search`) não se usa.
- **Nunca burlar anti-robô:** nada de stealth, troca de user-agent/IP, resolver captcha, imitar cabeçalhos internos
  para chamar API escondida. Se a loja bloqueia (403, captcha, Akamai/Cloudflare, conexão derrubada), PARE e diga
  ao dono que o caminho é o oficial (afiliado/feed ou pedir o arquivo de produtos à loja).
- Poucos acessos e com pausa (2-4 s). **Amazon:** nunca testar em massa (bloqueia o PC do dono).
- Nunca editar à mão `data/muquirana.db` nem `data.js`.
- Só vendedor confiável (a própria loja ou loja oficial da marca). Marketplace aberto: filtrar por loja oficial.

## 3. Montar o coletor
- Arquivo `collector/<loja>.py` no formato dos outros (ver `collector/lenovo.py` e `collector/samsung.py`): cada item
  tem `code, name, price, list_price, seller, img, url, available, offer_ends`. `price` = preço à vista/Pix.
- Catálogo inteiro: função `catalogo(path, pausa=...)`. Busca só se o robots.txt permitir.
- Loja com navegador: função `fechar()` (o `muq.py` fecha o navegador ao terminar cada loja).
- Ligar em `collector/muq.py` (`import` + dicionário `LOJAS`), na `collector/watchlist.json` (nome, `pausa`,
  `vendedores_confiaveis`, `not`, `catalogo` com `"fixa": true` quando a categoria da loja já é a certa, `onde`:
  `github` / `github-nav` / `pc`) e no `STORES` do `index.html` (nome, cor, domínio, busca da loja).
- Teste unitário em `tests/test_<loja>.py` (preço certo, indisponível/outro vendedor fica fora).

## 4. Conferir antes de publicar (obrigatório)
- Rodar o coletor local numa cópia: `MUQ_DB=<scratch>/x.db .venv/Scripts/python collector/muq.py coletar --lojas <loja>`.
- **Conferir pelo menos 5 preços** de produtos variados contra a página do produto no navegador (o preço "à vista
  no Pix"/"comprar"). Diferença de R$ 1 já é erro: ache a fonte que a ficha usa. Desconfie de produto com várias
  edições (o preço tem que ser da edição do nome).
- Olhar uma amostra de nomes: nada de DLC, acessório na categoria errada, kit "A + B", recondicionado.
- `.venv/Scripts/python -m unittest discover -s tests`.
- Workflow `testar-<loja>.yml` (só leitura, coleta numa cópia) para ver se a loja responde à rede do GitHub. Se o
  GitHub for bloqueado e o PC passar, use `"onde": "pc"`.

## 5. Publicar e documentar
- Commit em português, com a linha de coautoria, e `git push`. Disparar `gh workflow run "Coletar preços"` só se o
  dono quiser ver logo (cada coleta = 1 build do Cloudflare; limite 500/mês).
- Conferir no `data.js` (depois da coleta) a contagem da loja.
- Atualizar: tabela de lojas do `CLAUDE.md`, lista de lojas de `como-funciona.html`, `DIARIO.md` (o que foi feito e
  os preços conferidos) e `TAREFAS.md` se houver tarefa.
- Link de afiliado: só ligar depois de testar que o link **cai na página do produto** (o da Lenovo pela Lomadee caía
  na página inicial). Usar `rel="sponsored"` e manter a página de privacidade coerente.

## 6. Contar ao dono
Tabela curta: quantos produtos, quantos preços conferidos e se bateram, o que ficou de fora e por quê, e o que
depende dele (aprovação, chave, contato com a loja).
