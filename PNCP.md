# API PNCP — referência (oficial + o que já quebramos)

Baixado em 2026-09-01. Specs no repo:

| arquivo | origem |
|---|---|
| `docs/pncp-consulta-openapi.json` | `GET https://pncp.gov.br/api/consulta/v3/api-docs` |
| `docs/pncp-integracao-get-compras.json` | recorte GET de `https://pncp.gov.br/api/pncp/v3/api-docs` (itens/arquivos) |
| `docs/pncp-modalidades.json` | `GET https://pncp.gov.br/api/pncp/v1/modalidades` |

Swagger ao vivo:

- Consulta (pública): https://pncp.gov.br/api/consulta/swagger-ui/index.html
- Integração (write = Bearer): https://pncp.gov.br/api/pncp/swagger-ui/index.html
- Manual: https://pncp.gov.br/manual/pt-br/latest/singlehtml/

**Consulta não pede token.** Integração POST/PUT pede. GET de itens/arquivos em `/api/pncp/...` também passou sem auth (sessão 2026-09-01).

O OAS **não documenta o formato da data** (tipo `string` sem `format`). Na prática: **`yyyyMMdd`**. `2026-09-01` → 422.

## O que o buscador usa

Base: `https://pncp.gov.br/api/consulta`

### `GET /v1/contratacoes/publicacao` — recência

Obrigatório: `dataInicial`, `dataFinal`, **`codigoModalidadeContratacao`**, `pagina`.  
Opcional: `codigoModoDisputa`, **`uf`**, `codigoMunicipioIbge`, `cnpj`, `codigoUnidadeAdministrativa`, `idUsuario`, `tamanhoPagina` (**10–50**).

Não existe “todas as modalidades”. Loop nos códigos. `pncp_find.py` faz isso.

### `GET /v1/contratacoes/proposta` — ainda aberto

Obrigatório: **só** `dataFinal` + `pagina`.  
Não é janela de 24h. Credenciamento de 2023 com prazo até hoje aparece. **Não** é o default do CLI.

### `GET /v1/orgaos/{cnpj}/compras/{ano}/{sequencial}`

Detalhe. Mesmo payload da lista + `existeResultado`.

Paginação da lista: `data`, `totalRegistros`, `totalPaginas`, `numeroPagina`, `paginasRestantes`.

## Detalhe (integração GET, sem Bearer na prática)

```
GET /api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens
GET /api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos
GET /api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos/{n}   # PDF
GET /api/pncp/v1/modalidades
```

O GET da compra em `/api/pncp/v1/orgaos/.../compras/{ano}/{seq}` (sem `/itens`) devolveu **301** “endpoint movido” — usar a consulta.

## Modalidades (ids oficiais)

Ver `docs/pncp-modalidades.json`. As que o CLI varre por default: **6, 8, 7, 4, 5, 9**.

| id | nome |
|---|---|
| 4 | Concorrência - Eletrônica |
| 5 | Concorrência - Presencial |
| 6 | Pregão - Eletrônico |
| 7 | Pregão - Presencial |
| 8 | Dispensa |
| 9 | Inexigibilidade |

## Campos do JSON que o filtro lê

`objetoCompra`, `numeroControlePNCP`, `dataPublicacaoPncp`, `dataEncerramentoProposta`, `valorTotalEstimado`, `modalidadeNome`, `orgaoEntidade.{cnpj,razaoSocial}`, `unidadeOrgao.{ufSigla,municipioNome}`, `linkSistemaOrigem`, `anoCompra`, `sequencialCompra`.

## O que a consulta **não** tem (Licita Já tem no índice deles)

Keyword no servidor, valor min/max no query, porte de município, “smart search”. Por isso o CLI filtra **depois** de paginar.

## Rate limit

Não está no OAS. HTML `Limite de requisições excedido`, **sem** `Retry-After`. Mesmo IP.

O que **não** contorna: paralelo, outro User-Agent, rajada. Piora.

O que reduz tempo de parede:
- **janela de até 7 dias** numa paginação (`dataInicial`+`dataFinal`) em vez de 1 request por dia
- `requests.Session` (keep-alive)
- no 429: **uma** espera ~20s e pausa entre páginas sobe pra 1.2s
- `tamanhoPagina=50` (teto da consulta de contratação)

`pncp_coletar.py --dias 30` usa janelas de 7d e mods 6,8,4.

## Atualizar os JSON

```bash
curl -sS -o docs/pncp-consulta-openapi.json https://pncp.gov.br/api/consulta/v3/api-docs
curl -sS -o docs/pncp-modalidades.json https://pncp.gov.br/api/pncp/v1/modalidades
```
