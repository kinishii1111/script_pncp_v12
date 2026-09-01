---
name: pncp-nicho
description: >-
  Oportunidades PNCP no nicho hidrômetro/vazão/pressão. Coleta SQLite + filtro
  local. Use when: licitação, PNCP, edital 24h, oportunidade, Licita Já.
---

# PNCP nicho

Repo: `/home/kin/script_pncp_v12`. Não scrape o portal. Não abra o `.ipynb`.
Não rode `pncp_find.py` de novo se `data/coleta/pncp.db` já existe.

```bash
cd /home/kin/script_pncp_v12
# só se o db não existir ou estiver velho (>12h)
python3 pncp_coletar.py --horas 24
# testar filtro / gerar planilha (rápido)
python3 pncp_filtrar.py --xlsx ~/Downloads/pncp-revisao-24h.xlsx --json
```

Stdout JSON: `{corte, coletados, nicho, itens[]}`. Logs stderr.

Docs: `PNCP.md` (API), `LICITAJA.md` (filtros), `docs/SCRIPTS.md`, `PROCESSO.md`.
