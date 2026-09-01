#!/usr/bin/env python3
"""Coleta PNCP → SQLite (lento, retoma página). Não filtra nicho."""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from configurar_db import configurar_db
from fetch_retry import fetch_com_retry
from pncp_find import BASE, MODALIDADES, PAUSA, TAMANHO, TZ, yyyymmdd
from salvar_dados import inserir_dados, ler_progresso, marcar_progresso

DB_DEFAULT = Path(__file__).resolve().parent / "data" / "coleta" / "pncp.db"


def coletar_db(
    db: str,
    corte: datetime,
    pausa: float,
    mods: tuple[int, ...],
    uf: str | None = None,
) -> int:
    configurar_db(db)
    hoje = datetime.now(TZ)
    dias = sorted({yyyymmdd(corte), yyyymmdd(hoje)})
    total_novos = 0
    for dia in dias:
        for mod in mods:
            prev = ler_progresso(db, dia, mod)
            if prev and prev[0] >= prev[1] and prev[1] > 0:
                print(f"[skip] {dia} mod={mod} já completo p={prev[0]}/{prev[1]}", file=sys.stderr)
                continue
            pagina = (prev[0] + 1) if prev else 1
            total = prev[1] if prev else 1
            while pagina <= max(total, 1):
                params = {
                    "dataInicial": dia,
                    "dataFinal": dia,
                    "codigoModalidadeContratacao": mod,
                    "pagina": pagina,
                    "tamanhoPagina": TAMANHO,
                }
                if uf:
                    params["uf"] = uf
                ret = fetch_com_retry(BASE, params)
                if ret is None:
                    print(f"[warn] para em {dia} mod={mod} p={pagina} — rode de novo pra retomar", file=sys.stderr)
                    return total_novos
                dados, total_paginas = ret
                total = int(total_paginas or 1)
                n = inserir_dados(db, dados or [], pagina)
                total_novos += n
                marcar_progresso(db, dia, mod, pagina, total)
                print(f"[coleta] {dia} mod={mod} p={pagina}/{total} +{len(dados or [])}", file=sys.stderr)
                if pagina >= total:
                    break
                pagina += 1
                time.sleep(pausa)
            time.sleep(pausa)
    return total_novos


def main() -> int:
    ap = argparse.ArgumentParser(description="Coleta PNCP publicacao → SQLite (retomável).")
    ap.add_argument("--horas", type=int, default=24)
    ap.add_argument("--db", default=str(DB_DEFAULT))
    ap.add_argument("--pausa", type=float, default=PAUSA)
    ap.add_argument("--mods", default=",".join(str(m) for m in MODALIDADES))
    ap.add_argument("--uf", default=None, help="uma UF (vai na API)")
    args = ap.parse_args()
    mods = tuple(int(x) for x in args.mods.split(",") if x.strip())
    corte = datetime.now(TZ) - timedelta(hours=args.horas)
    n = coletar_db(args.db, corte, args.pausa, mods, uf=args.uf)
    print(f"[ok] novos={n} db={args.db}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
