# Referências de desenvolvimento

Este fork (`kinishii1111/script_pncp_v12`) parte do notebook do colega.
Não mesclar os outros repos na `main` sem decisão explícita.

## Remotes

| remote | repo | papel |
|---|---|---|
| `origin` | https://github.com/kinishii1111/script_pncp_v12 | nosso trabalho |
| `upstream` | https://github.com/flisboa999/script_pncp_v12 | colega — notebook v1.2 (TF-IDF + SGD, SQLite JSON1) |
| `referencia` | https://github.com/jose-cleiton/script_pncp | melhorias em cima da mesma ideia — **só leitura** (`push` desabilitado) |

```bash
git fetch referencia
git show referencia/main:pipeline.py
git show referencia/main:fetch_retry.py
```

Clone paralelo se precisar mexer sem misturar:

```bash
git clone https://github.com/jose-cleiton/script_pncp.git ../script_pncp-referencia
```

## O que puxar do Cleiton (e o que não)

Já viu o PNCP de verdade: `publicacao` vs `proposta`, data `yyyyMMdd`, modalidade 6, `tamanhoPagina=50`, **pausa 0,5s** (o 429 que tomamos no chat).

| arquivo no `referencia/main` | pra quê |
|---|---|
| `fetch_retry.py` | GET + backoff; trata 204/400/422/5xx. **Copiar cedo.** |
| `pipeline.py` | `PipelineConfig` + etapas coleta/rotular/treinar/classificar. `python main.py`. |
| `buscar_dados.py` / `pncp_client.py` / `configurar_db.py` | paginação e SQLite |
| `preprocessar.py` / `train.py` | mesmo SGD do notebook, já em .py |
| `classificar_gpt.py` | LLM opcional — **não** é o caminho default (cota) |
| notebooks BART / `classe_busca_*` | experimento; não é o núcleo |

Não puxar: `.env` com chave, DBs, notebooks de 400k, Gemini/GPT como filtro principal.

## Encaixe com o que já rodamos

- Gabarito positivo: `~/Downloads/dataset_2025.xlsx` (104 objetos, hidrômetro/vazão/pressão).
- Inferência alvo: publicação últimas 24h, não varrer 8k no chat.
- Itens/PDFs (CIS Itu, UFPR, CEGÁS) são etapa *depois* do filtro, não da coleta.

## Ordem

1. Coleta com retry/pausa do Cleiton (várias modalidades se precisar).
2. Treino com o xlsx do nicho + negativos do DB.
3. Classificar o dia → CSV/xlsx.
4. Só então itens + arquivos das que passaram.
