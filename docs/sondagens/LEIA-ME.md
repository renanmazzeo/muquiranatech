# Sondagens de lojas

Esta pasta é a ponte entre o agente autônomo (na nuvem) e os dois lugares onde a coleta roda de verdade.

| Arquivo | Quem escreve | Quem executa | Quando |
|---|---|---|---|
| `pedido-github.json` | agente | workflow `sondar.yml`, na rede do GitHub | logo após o push do pedido (uns 3 min) |
| `resultado-github.json` | robô do GitHub | | |
| `pedido-pc.json` | agente | `coletar-pc.ps1`, no PC do dono (IP residencial) | na próxima rodada do PC (a cada 6h, só com o PC ligado) |
| `resultado-pc.json` | robô do PC | | |

Para pedir um teste novo, **mude o `id`** do pedido (por exemplo, `2026-11-27-magalu-2`). Se o `id` for igual
ao do último resultado, o robô do PC não roda de novo.

Formato do pedido (detalhes em `collector/sondar.py`):
```json
{"id": "2026-11-27-magalu", "testes": [
  {"nome": "magalu-requests",  "url": "https://...", "modo": "requests"},
  {"nome": "magalu-navegador", "url": "https://...", "modo": "playwright"},
  {"nome": "amazon-coletor",   "loja": "amazon", "q": "echo-dot"}
]}
```
Cada resultado traz `funcionou`, `status`, `precos_na_pagina`, `exemplos_de_preco`, `bloqueio_detectado`,
`titulo` e `url_final`. "Funcionou" quer dizer: respondeu 200, sem tela de bloqueio, com pelo menos 3 preços na
página (ou um JSON com conteúdo). **Isso não basta para publicar a loja**: depois é preciso o coletor de verdade e a
conferência de 5 preços contra a página do produto.

Para uma loja passar a ser coletada pelo PC do dono, marque `"onde": "pc"` nela, em `lojas` no
`collector/watchlist.json`. O PC coleta todas as lojas marcadas assim, a cada 6h. O padrão, sem `onde`, é o GitHub.
