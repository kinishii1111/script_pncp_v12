"""INSERT OR IGNORE no SQLite. Log em stderr."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime

_SQL = """
INSERT OR IGNORE INTO contratacoes (pagina_coleta, timestamp_coleta, dados_json)
VALUES (?, ?, ?);
"""


def inserir_dados(nome_db: str, dados_pagina: list, pagina: int) -> int:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    n = 0
    with sqlite3.connect(nome_db) as conn:
        cur = conn.cursor()
        for reg in dados_pagina:
            cur.execute(_SQL, (pagina, ts, json.dumps(reg, ensure_ascii=False)))
            if cur.rowcount > 0:
                n += 1
        conn.commit()
    print(f"   [db] +{n}/{len(dados_pagina)} p={pagina}", file=sys.stderr)
    return n


def marcar_progresso(nome_db: str, dia: str, mod: int, pagina: int, total: int) -> None:
    with sqlite3.connect(nome_db) as conn:
        conn.execute(
            """INSERT INTO progresso (dia, mod, pagina, total) VALUES (?,?,?,?)
               ON CONFLICT(dia, mod) DO UPDATE SET pagina=excluded.pagina, total=excluded.total""",
            (dia, mod, pagina, total),
        )
        conn.commit()


def ler_progresso(nome_db: str, dia: str, mod: int) -> tuple[int, int] | None:
    with sqlite3.connect(nome_db) as conn:
        row = conn.execute(
            "SELECT pagina, total FROM progresso WHERE dia=? AND mod=?",
            (dia, mod),
        ).fetchone()
    return (int(row[0]), int(row[1])) if row else None


def ler_todos(nome_db: str) -> list[dict]:
    with sqlite3.connect(nome_db) as conn:
        rows = conn.execute("SELECT dados_json FROM contratacoes").fetchall()
    out = []
    for (raw,) in rows:
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return out
