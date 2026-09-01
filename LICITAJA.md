# Engenharia reversa: API Licita Já (BidHits) 1.1.4

Spec: https://app.swaggerhub.com/apis-docs/bidhits/licitaja-br/1.1.4  
OAS: `https://api.swaggerhub.com/apis/bidhits/licitaja-br/1.1.4`  
Base BR: `https://www.licitaja.com.br/api/v1` — **exige `X-API-KEY`** (assinatura). Sem chave, resultado incompleto. Não é o PNCP.

Não vamos chamar essa API no mini sistema (cota, login, dados deles). Copiamos o **produto**: filtros de busca que o colega já usa no Licita Já, aplicados em cima da consulta pública do PNCP.

## O que a API deles é

`GET /tender/search` — buscador com keyword + geografia + valor + data de abertura + modalidade.  
`GET /tender/{id}` — detalhe.  
`POST like / comment / erase` — CRM da conta, inútil pra nós.

Campo `number2` = número PNCP. Ou seja: o índice deles **aponta pro mesmo objeto** que já puxamos de graça.

## Espelho no `pncp_find`

| Licita Já | No nosso CLI | Fonte PNCP |
|---|---|---|
| `listing=0` novas | `--horas 24` | `/contratacoes/publicacao` |
| `opening_date_*` + `include_missing_dates` | `--abertos` | `dataEncerramentoProposta` (vazio entra) |
| `keyword` | léxico `data/nicho/` | `objetoCompra` |
| `smartsearch` (IA) | **não** | — |
| `state` | `--uf SP,PR` | query `uf` ou filtro local |
| `city` / `city_size` | **não** (porte IBGE depois, se doer) | `unidadeOrgao.municipioNome` |
| `type` | `--mods 6,8,4` | `codigoModalidadeContratacao` |
| `tender_value_min/max` | `--valor-min` `--valor-max` | `valorTotalEstimado` |
| `include_missing_values` | default inclui valor 0/null (exceto `--valor-min`) | |
| `date` catalogação | corte `--horas` em `dataPublicacaoPncp` | não é o banco deles |
| `order=1` registro | sort por `data_publicacao` | |
| `tender_summary` / `lots` | `--detalhe` futuro | `/itens` `/arquivos` |
| `url` | `link_pncp` | |
| `biddingPlatform` | `link_origem` | `linkSistemaOrigem` |
| like / comentário / informativo | **não** | CRM deles |

## O que não copiar

- Chave, trial, informativo diário por e-mail.
- “Busca inteligente” (termos gerados por AI no servidor deles).
- `city_size` sem tabela IBGE.
- Favorito/apagar — se um dia precisar, é coluna `ok` na planilha de revisão.

## Uso parecido com o buscador deles

```bash
python3 pncp_find.py --horas 24 --abertos --uf SP --valor-min 10000 --xlsx ~/Downloads/pncp-revisao-24h.xlsx --json
```
