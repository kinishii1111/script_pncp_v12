# Scripts

A geração “total” é lenta por causa do **429** do PNCP (8k registros, dezenas de páginas). **Não rode a coleta de novo pra testar léxico.**

| script | o quê | tempo |
|---|---|---|
| `pncp_coletar.py` | API → `data/coleta/pncp.db` (retoma página) | minutos |
| `pncp_filtrar.py` | DB + datasets → JSON/xlsx | segundos |
| `pncp_find.py` | atalho antigo (API na hora, sem cache) | minutos |

```bash
cd /home/kin/script_pncp_v12

# 30 dias, mods 6+8+4 (retoma se cair)
python3 pncp_coletar.py --dias 30
python3 pncp_status.py

python3 pncp_filtrar.py --dias 30 --xlsx ~/Downloads/pncp-revisao-30d.xlsx --json
```

`--mods 6,8` na coleta se quiser só pregão+dispensa (bem mais rápido).

Skill do agente: `SKILL.md` (repo) e `~/.grok/skills/pncp-nicho/`.
