"""Schema SQLite (JSON1). razaoSocial no JSON do PNCP é camelCase."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

_DDL = """
CREATE TABLE IF NOT EXISTS contratacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pagina_coleta INTEGER,
    timestamp_coleta TEXT,
    dados_json TEXT,
    pncp_id TEXT AS (json_extract(dados_json, '$.numeroControlePNCP')) STORED,
    orgao_nome TEXT AS (json_extract(dados_json, '$.orgaoEntidade.razaoSocial')) STORED,
    uf_sigla TEXT AS (json_extract(dados_json, '$.unidadeOrgao.ufSigla')) STORED,
    objeto_compra TEXT AS (json_extract(dados_json, '$.objetoCompra')) STORED,
    UNIQUE(pncp_id)
);
CREATE TABLE IF NOT EXISTS progresso (
    dia TEXT NOT NULL,
    mod INTEGER NOT NULL,
    pagina INTEGER NOT NULL,
    total INTEGER NOT NULL,
    PRIMARY KEY (dia, mod)
);
"""
_IDX = [
    "CREATE INDEX IF NOT EXISTS idx_pncp_id ON contratacoes (pncp_id);",
    "CREATE INDEX IF NOT EXISTS idx_uf ON contratacoes (uf_sigla);",
]


def configurar_db(nome_db: str) -> None:
    Path(nome_db).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(nome_db) as conn:
        conn.executescript(_DDL)
        for q in _IDX:
            conn.execute(q)
        conn.commit()
    print(f"[db] {nome_db}", file=sys.stderr)


if __name__ == "__main__":
    configurar_db(sys.argv[1] if len(sys.argv) > 1 else "data/coleta/pncp.db")
