#!/usr/bin/env python3
"""Filtra o SQLite da coleta com o léxico do nicho. Rápido — não chama a API."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from pncp_find import (
    TZ,
    carregar_dataset,
    enriquece,
    extra_frases,
    fold,
    gravar_xlsx,
    parse_dt,
    pontuar,
    resolver_datasets,
)
from salvar_dados import ler_todos

DB_DEFAULT = Path(__file__).resolve().parent / "data" / "coleta" / "pncp.db"


def main() -> int:
    ap = argparse.ArgumentParser(description="Filtra coleta PNCP (SQLite) pelo nicho.")
    ap.add_argument("--db", default=str(DB_DEFAULT))
    ap.add_argument("--dataset", action="append", dest="datasets")
    ap.add_argument("--horas", type=int, default=None)
    ap.add_argument("--dias", type=int, default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--xlsx")
    ap.add_argument("--abertos", action="store_true")
    ap.add_argument("--min-score", type=int, default=3)
    ap.add_argument("--uf")
    ap.add_argument("--valor-min", type=float, dest="valor_min")
    ap.add_argument("--valor-max", type=float, dest="valor_max")
    ap.add_argument("--keyword")
    ap.add_argument("--cidade")
    ap.add_argument("--ordem", choices=("score", "pub", "encerramento", "valor", "uf"), default="score")
    ap.add_argument(
        "--sem-nicho",
        action="store_true",
        help="ignora léxico hidrômetro; filtra só --keyword (e UF/valor/cidade)",
    )
    args = ap.parse_args()

    db = Path(args.db)
    if not db.exists():
        print(f"sem coleta: {db} — rode python3 pncp_coletar.py primeiro", file=sys.stderr)
        return 2

    arquivos: list = []
    extras: list[str] = []
    if not args.sem_nicho:
        arquivos = resolver_datasets(args.datasets)
        textos: list[str] = []
        for ds in arquivos:
            textos.extend(carregar_dataset(ds))
        seen: set[str] = set()
        uniq = []
        for t in textos:
            k = fold(t)
            if k not in seen:
                seen.add(k)
                uniq.append(t)
        extras = extra_frases(uniq)
        print(f"[nicho] {len(uniq)} textos db={db}", file=sys.stderr)
    elif not args.keyword:
        print("--sem-nicho exige --keyword", file=sys.stderr)
        return 2

    agora = datetime.now(TZ)
    horas = args.dias * 24 if args.dias else (args.horas if args.horas is not None else 24)
    corte = agora - timedelta(hours=horas)
    ufs = [u.strip().upper() for u in (args.uf or "").split(",") if u.strip()]
    keywords = [fold(k) for k in (args.keyword or "").split(",") if k.strip()]
    cidades = [fold(c) for c in (args.cidade or "").split(",") if c.strip()]

    bruto = ler_todos(str(db))
    hits_out = []
    for it in bruto:
        pub = parse_dt(it.get("dataPublicacaoPncp") or it.get("dataInclusao"))
        if not pub or pub < corte:
            continue
        obj = it.get("objetoCompra") or ""
        fo = fold(obj)
        if args.sem_nicho:
            if not any(k in fo for k in keywords):
                continue
            hits = [k for k in keywords if k in fo]
            sc = 3 * len(hits)
        else:
            sc, hits = pontuar(obj, extras)
            if sc < args.min_score or hits == ["bloqueio"]:
                continue
            if keywords and not any(k in fo for k in keywords):
                continue
        if args.abertos:
            enc = parse_dt(it.get("dataEncerramentoProposta"))
            if enc is not None and enc < agora:
                continue
        u = (it.get("unidadeOrgao") or {}).get("ufSigla") or ""
        if ufs and u.upper() not in ufs:
            continue
        mun = fold((it.get("unidadeOrgao") or {}).get("municipioNome") or "")
        if cidades and not any(c in mun for c in cidades):
            continue
        val = it.get("valorTotalEstimado")
        if args.valor_min is not None and (not isinstance(val, (int, float)) or val < args.valor_min):
            continue
        if args.valor_max is not None and isinstance(val, (int, float)) and val > args.valor_max:
            continue
        hits_out.append(enriquece(it, sc, hits, pub))

    if args.ordem == "pub":
        hits_out.sort(key=lambda r: r.get("data_publicacao") or "")
    elif args.ordem == "valor":
        hits_out.sort(key=lambda r: -(r["valor_estimado"] if isinstance(r.get("valor_estimado"), (int, float)) else -1))
    else:
        hits_out.sort(key=lambda r: -r["score"])

    payload = {
        "corte": corte.isoformat(),
        "coletados": len(bruto),
        "nicho": len(hits_out),
        "datasets": [str(p) for p in arquivos],
        "db": str(db),
        "itens": hits_out,
    }
    if args.xlsx:
        gravar_xlsx(hits_out, Path(args.xlsx).expanduser(), meta=payload)
        print(f"[xlsx] {args.xlsx}", file=sys.stderr)
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
