#!/usr/bin/env python3
"""Coleta PNCP → SQLite (lento, retoma página). Não filtra nicho."""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from configurar_db import configurar_db
from fetch_retry import fetch_com_retry, pausa_sugerida
from pncp_find import BASE, PAUSA, TAMANHO, TZ, listar_janelas
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
    janelas = listar_janelas(corte, tamanho=7)
    total_novos = 0
    print(f"[coleta] {len(janelas)} janelas de 7d mods={mods}", file=sys.stderr)
    import fetch_retry as fr

    for ini, fim in janelas:
        chave = f"{ini}_{fim}"
        for mod in mods:
            prev = ler_progresso(db, chave, mod)
            if prev and prev[0] >= prev[1] and prev[1] > 0:
                print(f"[skip] {chave} mod={mod}", file=sys.stderr)
                continue
            pagina = (prev[0] + 1) if prev else 1
            total = prev[1] if prev else 1
            falhou = False
            while pagina <= max(total, 1):
                params = {
                    "dataInicial": ini,
                    "dataFinal": fim,
                    "codigoModalidadeContratacao": mod,
                    "pagina": pagina,
                    "tamanhoPagina": TAMANHO,
                }
                if uf:
                    params["uf"] = uf
                ret = fetch_com_retry(BASE, params)
                if ret is None:
                    print(
                        f"[warn] {chave} mod={mod} p={pagina} — segue, retoma depois",
                        file=sys.stderr,
                    )
                    falhou = True
                    break
                dados, total_paginas = ret
                total = int(total_paginas or 1)
                n = inserir_dados(db, dados or [], pagina)
                total_novos += n
                marcar_progresso(db, chave, mod, pagina, total)
                print(
                    f"[coleta] {chave} mod={mod} p={pagina}/{total} +{len(dados or [])}",
                    file=sys.stderr,
                )
                if pagina >= total:
                    break
                pagina += 1
                time.sleep(max(pausa, fr.pausa_sugerida))
            if not falhou:
                time.sleep(0.2)
    return total_novos


def main() -> int:
    ap = argparse.ArgumentParser(description="Coleta PNCP publicacao → SQLite (retomável).")
    ap.add_argument("--horas", type=int, default=None)
    ap.add_argument("--dias", type=int, default=None, help="atalho: horas = dias*24 (ex. 30)")
    ap.add_argument("--db", default=str(DB_DEFAULT))
    ap.add_argument("--pausa", type=float, default=PAUSA)
    ap.add_argument(
        "--mods",
        default="6,8,4",
        help="default 6,8,4 (pregão e / dispensa / concorrência e) — menos 429",
    )
    ap.add_argument("--uf", default=None, help="uma UF (vai na API)")
    args = ap.parse_args()
    mods = tuple(int(x) for x in args.mods.split(",") if x.strip())
    if args.dias:
        horas = args.dias * 24
    else:
        horas = args.horas if args.horas is not None else 24
    corte = datetime.now(TZ) - timedelta(hours=horas)
    n = coletar_db(args.db, corte, args.pausa, mods, uf=args.uf)
    print(f"[ok] novos={n} db={args.db}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
