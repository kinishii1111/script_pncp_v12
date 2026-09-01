#  Pipeline de NLP para Classificação de Licitações (API do PNCP)

Este projeto implementa um *pipeline* de engenharia de dados e ML para ingestão, processamento e classificação de licitações do Portal Nacional de Contratações Públicas (PNCP), utilizando `Python`, `SQLite` e `Scikit-learn`.

O objetivo é filtrar um *stream* de dados de alto volume (milhares de licitações diárias) e classificá-lo em `1` (Relevante) ou `0` (Irrelevante), reduzindo o esforço de análise manual para prospecção de BI em mais de 95%.

### Stack de Tecnologia

* **Ingestão/Armazenamento:** `requests`, `sqlite3` (com extensão `JSON1`)
* **ETL/Processamento:** `pandas`, `re` (Regex)
* **NLP/Modelagem:** `nltk` (stopwords), `scikit-learn` (`Pipeline`, `TfidfVectorizer`, `SGDClassifier`)
* **Serialização:** `joblib`

**O que isto substitui no processo manual (sessão 2026-09-01):** ver `PROCESSO.md`.  
**Remotes:** `REFERENCIA.md` (colega = `upstream`, Cleiton = `referencia` só leitura).

### Tool de agente (sem Jupyter)

```bash
python3 pncp_find.py --horas 24 --json
# usa data/nicho/dataset_2024.xlsx + dataset_2025.xlsx (2023 no zip veio sem texto)
```

Stdout JSON. Skill: `SKILL.md`. O notebook do colega fica como origem do SGD — só entra quando houver classe `0`.

---

## Arquitetura e Decisões de Implementação (.)

O *notebook* `.` é refatorado para uma arquitetura modular e sequencial, separando **Configuração**, **Definição** e **Ação**.

### 1. Lógica de Execução (O *Runbook*)

A execução segue 5 etapas lógicas para garantir reprodutibilidade e facilitar o *debug*:

1.  **Etapa 0: Configuração (Células 1-2)**
    * Todos os `import` de bibliotecas e variáveis globais (`NOME_DB_PRODUCAO`, `ARQUIVOS_CSV_POSITIVOS`, `IDS_RELEVANTES_CADERNO`, etc.) são centralizados no início do *notebook*.

2.  **Etapa 1: Definição das Ferramentas (Células 3-6)**
    * Apenas a *definição* (`def`) das funções-chave é executada, carregando as "receitas" na memória sem rodá-las.
    * `configurar_db`: Prepara o *schema* do SQLite.
    * `fetch_com_retry` / `inserir_dados` / `buscar_dados_paginados`: Funções de coleta da API.
    * `preprocessar_texto`: O "liquidificador" de NLP.

3.  **Etapa 2: Ação de Coleta (Célula 7 - Opcional)**
    * **Botão de Ação 1.** Executa `buscar_dados_paginados` para popular os bancos de dados (`pncp_data_...db`). Esta célula é separada e opcional, pois os dados de produção (19.9k) só precisam ser baixados uma vez.

4.  **Etapa 3: Ação de ETL de Treino (Célula 8)**
    * **Botão de Ação 2.** Constrói o "gabarito" (`dataset.csv`). Ele orquestra o `pandas` para:
        1.  Ler os `1`s (Relevantes) dos `ARQUIVOS_CSV_POSITIVOS`.
        2.  Ler o `NOME_DB_TREINO_NEGATIVOS` (`pncp_data_500.db`).
        3.  Aplicar os rótulos do `IDS_RELEVANTES_CADERNO` (ex: `[5, 85, ...]`) usando `.apply()`.
        4.  Limpar dados corrompidos (filtros `.dropna()` e `.str.contains('BLOB')`).
        5.  Fundir (`.concat()`) e deduplicar (`.drop_duplicates()`) as fontes.

5.  **Etapa 4: Ação de Treinamento (Célula 9)**
    * **Botão de Ação 3.** Carrega o `dataset.csv` (gabarito) e executa o *pipeline* de ML.
    * Salva o "cérebro" treinado (`modelo_relevancia.joblib`) usando `joblib.dump()`.

6.  **Etapa 5: Ação de Produção/Inferência (Célula 10)**
    * **Botão de Ação 4.** Carrega o `modelo_relevancia.joblib` e o aplica no *dataset* de produção (`NOME_DB_PRODUCAO`).
    * O resultado (o "filé") é salvo em um banco de dados final: `NOME_DB_FILTRADO`.

### 2. Decisões de Engenharia de Elite

* **`sqlite3` com `JSON1` (Célula 3):** Em vez de parsear o JSON em Python, usamos `AS (json_extract(dados_json, '$.objetoCompra')) STORED`. O próprio SQLite extrai o texto do objeto no momento da inserção. Isso desacopla o *data lake* (o JSON bruto) do *data warehouse* (a coluna `objeto_compra` indexada), tornando a coleta rápida e as consultas de ML eficientes.

* **`TfidfVectorizer(ngram_range=(1, 2))` (Célula 9):** O modelo não aprende apenas palavras isoladas (`'vazão'`), mas também o contexto de bigramas (`'medidor vazão'`, `'sensor nível'`). Isso aumenta exponencialmente a capacidade do modelo de diferenciar ruído de sinal.

* **`SGDClassifier(class_weight='balanced')` (Célula 9):** Esta é a correção para o "modelo preguiçoso". Como o *dataset* é naturalmente desbalanceado (mais `0`s que `1`s), `balanced` aplica uma penalidade maior para erros na classe `1` (Relevante). Isso força o modelo a otimizar para **Recall** (achar o filé) em vez de Acurácia (chutar `0` sempre).

* **`pd.read_sql_query(chunksize=2000)` (Célula 10):** Esta é a solução de **escalabilidade**. O protótipo `v4` falhava ao carregar 19.9k+ itens na RAM. A `.` lê o DB de produção em "lotes" de 2000 linhas, processa, filtra e descarta o lixo da memória, permitindo a análise de *datasets* de tamanho ilimitado com uso de RAM baixo e constante.

---
---

## Changelog: Melhorias de v4 para .

* **Modularidade:** Código refatorado de um *notebook* caótico (`v0.4`) para 5 etapas sequenciais e lógicas (`v1.2`), separando Configuração, Definição de Funções e Ações (Coleta, Treino, Produção).

* **ETL de Treino:** Corrigido o erro fatal `got 1 class`. O *pipeline* (`Célula 8`) agora constrói um *dataset* de gabarito (`dataset.csv`) funcional, mesclando CSVs de `1`s e um DB de amostra de `0`s.

* **Limpeza de Dados:** Adicionados filtros explícitos (`.dropna()`, `.str.contains('BLOB')`) para remover dados corrompidos (BLOBs ou Nulos) durante o ETL de treino e produção.

* **Eficácia do Modelo:** Implementado `class_weight='balanced'` no `SGDClassifier` (`Célula 9`) para corrigir o "modelo preguiçoso", elevando o **Recall de 79% (v4) para 95% (.)**.

* **Features de NLP:** `TfidfVectorizer` atualizado de `ngram_range=(1, 1)` para `(1, 2)`, permitindo ao modelo aprender o contexto de pares de palavras.

* **Escalabilidade:** Implementado processamento em lotes (`chunksize=2000`) na célula de produção (`Célula 10`), permitindo que o modelo filtre *datasets* massivos (19.9k+) sem estourar a memória RAM.