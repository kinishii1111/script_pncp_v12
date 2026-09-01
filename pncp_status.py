#!/usr/bin/env python3
"""Status da coleta SQLite."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parent / "data" / "coleta" / "pncp.db"


def main() -> int:
    db = Path(sys.argv[1] if len(sys.argv) > 1 else DB)
    if not db.exists():
        print("sem db", db)
        return 2
    with sqlite3.connect(db) as conn:
        n = conn.execute("SELECT COUNT(*) FROM contratacoes").fetchone()[0]
        prog = conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN pagina>=total AND total>0 THEN 1 ELSE 0 END) FROM progresso"
        ).fetchone()
        incompletos = conn.execute(
            "SELECT dia, mod, pagina, total FROM progresso WHERE pagina<total OR total=0 ORDER BY dia, mod"
        ).fetchall()
    tot, ok = prog[0] or 0, prog[1] or 0
    print(f"db={db}")
    print(f"registros={n} fatias={ok}/{tot} completas")
    for row in incompletos[:20]:
        print(f"  incompleto {row[0]} mod={row[1]} p={row[2]}/{row[3]}")
    if len(incompletos) > 20:
        print(f"  ... +{len(incompletos)-20}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
