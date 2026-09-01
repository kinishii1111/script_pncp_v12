# O que o repo agilizou vs o que fizemos na mão

Sessão 2026-09-01. Portal PNCP aberto, sem token. Objetivo: oportunidades do **nicho de instrumentação** (hidrômetro, macromedidor, vazão, pressão, calibração) nas últimas 24h.

## O que foi manual (chat + curl)

1. **Mapear a API**  
   Swagger `https://pncp.gov.br/api/consulta/v3/api-docs`. Consulta = GET público. `/api/pncp` write = Bearer (órgão). Sem session cookie.

2. **Descobrir as pegadinhas na porrada**  
   Data `yyyyMMdd` (ISO dá 422). `tamanhoPagina` 10–50. `publicacao` **exige** modalidade (não existe “todas”). `proposta` só `dataFinal`. Rajada = **HTTP 429**. Página 1 de ontem caiu timeout/502.

3. **Ler o gabarito do colega**  
   `dataset_2025.xlsx`: 104 `y=1`, zero `0`. Vocabulário: hidrômetro, macromedidor, transmissor, SAAE/ETA/ETE.  
   Depois `dataset_2024.xlsx` (93 úteis) e `dataset_2023.xlsx` (**vazio**: export Google com `REGEXREPLACE`, coluna A sem valor).

4. **Varrer 31/08 + 01/09**  
   Mods 6,8,7,4,5,9. ~167 páginas, **8041** publicações, **5818** nas 24h. Score por regex no `objetoCompra`. Sem o retry/pausa do colega: sleep ad hoc e ainda 429.

5. **Triagem humana**  
   Regex frouxo puxou decibelímetro, reômetro, quadro elétrico. Sobraram 3 que encaixam:
   - CIS Itu — RP hidrômetros, R$ 1,32 mi, PE 32/2026 (saiu 31/08 08:22, **fora do corte 24h rígido**, ainda aberto 16/09)
   - UFPR Maripá — hidrômetro tangencial DN150 + instalação, R$ 4.600, dispensa
   - CEGÁS — calibração rotativo/turbina **gás**, lab RBC/17025, PE 20260007

6. **Fornecedor (ainda não é o CLI)**  
   `GET /itens` + `/arquivos`, download PDF, `pdftotext`. Spec CIS: unijato 3/4 Q3 1,0 × 12.000 un, INMETRO 155/2022, logo CIS. Planilha `~/Downloads/pncp-nicho-24h.xlsx` + pasta `pncp-nicho-docs/`.

Custo: dezenas de minutos de agente, JSON no `/tmp`, nada reproduzível num comando.

## O que o repo (colega + Cleiton + este fork) agilizou

Não reinventar o pescador. O notebook do colega e o Python do Cleiton **já tinham** o que o chat teve que descobrir:

| Na mão | No repo (já existia) | No fork agora |
|---|---|---|
| OpenAPI + trial-and-error de data/modalidade | `pipeline.py`: `publicacao`/`proposta`, `yyyyMMdd`, mod 6, página 50 | `pncp_find.py` usa isso |
| Retry 429 escrito no chat | `fetch_retry.py` (backoff, 204/400/422/5xx) | copiado; 429 espera ≥8s; log em **stderr** (stdout = JSON do agente) |
| Pausa no feeling | `pausa_entre_paginas=0.5` | default 0.7 |
| SQLite JSON1 (não usamos no chat) | `configurar_db.py` | próximo passo, não bloqueia o find |
| Gabarito 1/0 no Excel | mesmo schema `texto_bruto,x,y` | `data/nicho/` 2024+2025 (190 textos). 2023 ignorado vazio |
| SGD no notebook | Célula 9 TF-IDF+SGD `class_weight=balanced` | **não ligado**: só tem classe 1 (`got 1 class`) |
| Jupyter | Cleiton já virou `main.py` | nós **não** usamos Jupyter; CLI único |
| 15 min de tool-loop | — | `python3 pncp_find.py --horas 24 --json` |

Prova do CLI (pregão, 24h, léxico com gate): 814 coletados; sem gate = 131 lixo de “registro de preços”; **com gate de frase do nicho = 1** (CEGÁS). CIS continua fora das 24h — o corte é honesto.

## O que ainda é manual (de propósito)

- Itens, TR, PDF, busca de fornecedor (CIS 12 mil unijato, lab RBC CEGÁS).
- Julgar borda (gás vs água, dispensa UFPR).
- Rebaixar 2023 **com valores**.
- Rotular `0` num dump do dia se um dia formos treinar SGD.

## Comando canônico (agente)

```bash
cd /home/kin/script_pncp_v12
python3 pncp_find.py --horas 24 --json
```

Skill: `SKILL.md`. Remotes: `REFERENCIA.md`. Não scrape `pncp.gov.br` HTML. Não abra `script_pncp_v12.ipynb` pra achar edital.

## Caminho da demanda (editais recentes × nicho)

Demanda: **os mais novos que encaixam no dataset**, pra agente achar — não varrer portal.

```
API publicacao (N horas)  →  léxico dataset  →  JSON/xlsx  →  (depois) itens/PDF
```

| passo | status | o que é |
|---|---|---|
| 1. Coleta 24h + retry | **pronto** | `pncp_find.py` — `fetch_retry` do Cleiton |
| 2. Filtro nicho (frase forte) | **pronto** | 2024+2025 em `data/nicho/`; 2023 vazio |
| 3. Ainda disputável | **pronto** | `--abertos` (encerra no futuro; sem data entra) |
| 4. Planilha | **pronto** | `--xlsx saida.xlsx` |
| 5. Itens + TR só do que passou | próximo | `--detalhe` → GET itens/arquivos |
| 6. Cache do dia | depois | SQLite JSON1 do colega, não re-paginar |
| 7. SGD | só com `0` | dump do dia rotulado; senão esquece |

Comando da demanda:

```bash
python3 pncp_find.py --horas 24 --abertos --json --xlsx ~/Downloads/pncp-nicho-24h.xlsx
# opcional, espelho Licita Já: --uf SP --valor-min 10000
```

`--modo proposta` do Cleiton **não** é “últimas 24h” (mistura credenciamento velho). Recência = `publicacao` + corte de horas. Oportunidade viva = `--abertos`. Filtros de produto do Licita Já: `LICITAJA.md`.
