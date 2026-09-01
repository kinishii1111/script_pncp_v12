# Scripts

A geração “total” é lenta por causa do **429** do PNCP (8k registros, dezenas de páginas). **Não rode a coleta de novo pra testar léxico.**

| script | o quê | tempo |
|---|---|---|
| `pncp_coletar.py` | API → `data/coleta/pncp.db` (retoma página) | minutos |
| `pncp_filtrar.py` | DB + datasets → JSON/xlsx | segundos |
| `pncp_find.py` | atalho antigo (API na hora, sem cache) | minutos |

```bash
cd /home/kin/script_pncp_v12

# 1x (ou de novo se caiu no meio — retoma)
python3 pncp_coletar.py --horas 24

# N vezes, barato
python3 pncp_filtrar.py --xlsx ~/Downloads/pncp-revisao-24h.xlsx --json
python3 pncp_filtrar.py --abertos --uf SP --json
```

`--mods 6,8` na coleta se quiser só pregão+dispensa (bem mais rápido).

Skill do agente: `SKILL.md` (repo) e `~/.grok/skills/pncp-nicho/`.
