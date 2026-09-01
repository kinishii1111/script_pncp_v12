---
name: pncp-nicho
description: >-
  PNCP: coleta SQLite + filtro local (hidrômetro, Adobe/Canva, sites, keyword).
  Use when: licitação, edital, PNCP, oportunidade, 24h, 30 dias, software, Canva, Adobe, desenvolvimento de site.
---

# PNCP

Repo: `/home/kin/script_pncp_v12`. Consulta pública, sem token. Sem scrape HTML, sem Jupyter, sem TinyFish, sem gov.br pra furar 429.

**Coleta é lenta. Filtro é local.** Se `data/coleta/pncp.db` existe, **não** rode `pncp_coletar` / `pncp_find` só pra mudar keyword.

```bash
cd /home/kin/script_pncp_v12
python3 pncp_status.py
```

## Filtro (segundos)

Stdout JSON `{corte, coletados, nicho, itens[]}`. Logs stderr. Xlsx em `~/Downloads/`.

```bash
# nicho hidrômetro/vazão (datasets data/nicho/)
python3 pncp_filtrar.py --dias 30 --xlsx ~/Downloads/pncp-revisao-30d.xlsx --json

# outro tema (sem léxico de hidrômetro)
python3 pncp_filtrar.py --dias 30 --sem-nicho --keyword "adobe,canva,acrobat" \
  --xlsx ~/Downloads/pncp-software-adobe-canvas.xlsx --json

python3 pncp_filtrar.py --dias 30 --sem-nicho \
  --keyword "desenvolvimento de site,website,site institucional,desenvolvimento web" \
  --xlsx ~/Downloads/pncp-sites-web.xlsx --json
```

`--sem-nicho` **exige** `--keyword` (vírgula = OU). `--uf SP` `--abertos` `--valor-min` depois do dump, sem API.

Canva no BR é **Canva**, não Canvas (LMS).

## Coleta (só se db sumiu ou período novo)

```bash
python3 pncp_coletar.py --dias 30          # default mods 6,8,4; retoma; janela 7d
# caiu? o mesmo comando de novo. 429 = espera, não paralelo.
```

## Depois do filtro (um id)

`numero_pncp` = `cnpj-1-seq/ano`

`GET https://pncp.gov.br/api/consulta/v1/orgaos/{cnpj}/compras/{ano}/{seq}`  
`GET https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens`  
`GET .../arquivos`

## Docs no repo (não copiar pra cá)

`PNCP.md` API · `LICITAJA.md` filtros · `docs/SCRIPTS.md` · `PROCESSO.md`
