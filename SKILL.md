---
name: pncp-nicho
description: >-
  Achados PNCP das últimas horas no nicho do dataset (hidrômetro, vazão, pressão).
  API consulta pública, sem token. Use when: licitação, PNCP, oportunidade, edital 24h.
---

# PNCP nicho (agente)

Não scrape o portal. Não abra o `.ipynb`.

```bash
cd /home/kin/script_pncp_v12
python3 pncp_find.py --horas 24 --abertos --json
# gabarito: data/nicho/ (2024+2025). --xlsx opcional.
```

Stdout = JSON `{corte, coletados, nicho, itens[]}`. Logs em stderr.

Cada item: `numero_pncp`, `objeto`, `orgao`, `uf`, `valor_estimado`, `link_pncp`, `score`.

Detalhe/itens/PDF (depois do filtro):

`GET https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens`  
`GET .../arquivos`

Pausa entre páginas já está no script (429). Não paralelizar rajada.

Contexto do que era manual: `PROCESSO.md`.
