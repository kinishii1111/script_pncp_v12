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

`--mods 6,8` na coleta se quiser só pregão+dispensa.

Outro tema no **mesmo** DB (`--sem-nicho`):

```bash
python3 pncp_filtrar.py --dias 30 --sem-nicho --keyword "adobe,canva" --xlsx ~/Downloads/pncp-software-adobe-canvas.xlsx --json
python3 pncp_filtrar.py --dias 30 --sem-nicho --keyword "desenvolvimento de site,website,site institucional" --xlsx ~/Downloads/pncp-sites-web.xlsx --json
```

Skill: `SKILL.md` (repo = fonte) e `~/.grok/skills/pncp-nicho/` (espelho).
