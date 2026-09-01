# Checkpoint PNCP — 2026-09-01

**Status:** POC no ar. Coleta 30d **parou com buracos**. Filtro local ok.

## Onde

- Fork: https://github.com/kinishii1111/script_pncp_v12 · disco `/home/kin/script_pncp_v12`
- DB: `data/coleta/pncp.db` — **35 591** registros (mods 6,8,4; janelas 7d)
- Skill: `SKILL.md` + `~/.grok/skills/pncp-nicho/`

## Buracos da coleta (retomar `pncp_coletar.py --dias 30`)

- `20260802_20260808` mod 8: 73/262
- `20260809_20260815` mod 8: 233/305
- `20260830_20260901` mod 8: 72/93
- concorrência última janela nem começou
- fatia velha `20260804` mod 6: 5/35 (chave antiga, ignora)

## Prova (Downloads)

| arquivo | o quê |
|---|---|
| `pncp-revisao-24h.xlsx` | 4 linhas 24h (UFPR, SAAE RN, Parapuã FP, CEGÁS) |
| `pncp-revisao-30d.xlsx` | 39 linhas nicho hidrômetro; tem FP score 3 |
| `pncp-software-adobe-canvas.xlsx` | 32 Adobe/Canva |
| `pncp-sites-web.xlsx` | 24 sites (score 6 = dev de verdade) |
| `pncp-nicho-docs/` | PDFs CIS/UFPR/CEGÁS da sessão manual |

## Funciona

- `pncp_filtrar.py` no SQLite, segundos, **sem API**
- `--sem-nicho --keyword` pra outro tema
- `numeroControlePNCP` → GET itens/arquivos
- Léxico hidrômetro: `data/nicho/` 2024+2025 (190). 2023 xlsx **vazio** (export fórmula)

## Decisão

- Não Licita Já paga, não TinyFish, não gov.br pra 429
- Recência = `publicacao` + horas; `--abertos` = ainda disputa
- SGD só com `ok=0` na planilha; gabarito hoje só classe 1

## Próximo

1. Colega marca `ok` nas xlsx (30d hidrômetro + ruído score 3)
2. Opcional: `pncp_coletar.py --dias 30` retoma buracos de dispensa → filtrar de novo
3. `--detalhe` (itens/PDF) só das linhas `ok=1`

## Fora

Jupyter, scrape HTML, paralelo na API, treinar SGD no dump cru.
