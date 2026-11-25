# MuquiranaTech

Portal de ofertas de tecnologia que compara o preço de hoje com o histórico.

## Estrutura
- `index.html`: o site. Lê `data.js` e, se ele não existir, mostra dados fictícios.
- `collector/muq.py`: coletor de preços.
- `collector/watchlist.json`: o que monitorar (buscas, categorias, vendedores confiáveis).
- `data/muquirana.db`: banco SQLite com o preço de cada dia (`source` = `live` ou `wayback`).
- `.github/workflows/coletar.yml`: coleta automática 2x por dia + histórico Wayback aos domingos.

## Rodar localmente (Windows)
```powershell
python -m venv .venv
.venv\Scripts\pip install -r collector\requirements.txt
.venv\Scripts\python collector\muq.py tudo        # coleta hoje + gera data.js
.venv\Scripts\python collector\muq.py historico   # histórico da Wayback (precisa acessar web.archive.org)
.venv\Scripts\python collector\muq.py exportar
```
Depois é só abrir `index.html` no navegador.

## Fontes
| Loja | Status |
|---|---|
| KaBuM! | ✅ páginas de busca (vendedor KaBuM!, Magalu ou Fast Shop) |
| Wayback Machine | ✅ histórico a partir das páginas de categoria/busca arquivadas |
| Mercado Livre | ⏳ API gratuita, precisa de credenciais de app |
| Pichau, Terabyte, Magalu | ⛔ bloqueiam robôs (Cloudflare/403), avaliar programas de afiliado |
