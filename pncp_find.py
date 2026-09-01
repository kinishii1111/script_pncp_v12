#!/usr/bin/env python3
"""CLI para agentes: PNCP últimas N horas, filtrado pelo dataset de nicho.

Uso:
  python3 pncp_find.py --dataset ~/Downloads/dataset_2025.xlsx --horas 24 --json
  python3 pncp_find.py --dataset dataset_2025.xlsx --horas 24 --xlsx /tmp/out.xlsx
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fetch_retry import fetch_com_retry

BASE = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
# pregão e, conc, presencial, dispensa, inexig — volume vs sinal
MODALIDADES = (6, 8, 7, 4, 5, 9)
TAMANHO = 50
PAUSA = 0.7
TZ = timezone(timedelta(hours=-3))

# ruído que o léxico pega (decibelímetro, odonto, etc.)
BLOQUEIO = (
    r"decibel",
    r"bafomet",
    r"alcoolem",
    r"odont",
    r"esfigmo",
    r"reometro",
    r"ginecolog",
    r"instrumentais de",
    r"opme",
    r"audiovisual",
)

# frases do nicho (dataset 2025: hidrometria / instrumentação água-gás)
FORTE = (
    r"macromedidor",
    r"macro[\s-]?medidor",
    r"hidrometr",
    r"hidrometro",
    r"medidor(?:es)? de vazao",
    r"medidor(?:es)? de fluxo",
    r"medidor(?:es)? eletromagnet",
    r"medidor(?:es)? ultrasson",
    r"transmissor(?:es)? de pressao",
    r"transmissor(?:es)? de nivel",
    r"sensor(?:es)? de nivel",
    r"sensor(?:es)? de pressao",
    r"pitometr",
    r"rotametro",
    r"clamp[\s-]?on",
    r"calha parshall",
    r"woltmann",
    r"unijato",
    r"multijato",
    r"instrumentacao",
    r"telemetria",
    r"medidor(?:es)? de pressao",
)


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower())


def carregar_dataset(path: Path) -> list[str]:
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    textos = []
    rows = ws.iter_rows(values_only=True)
    next(rows, None)
    for row in rows:
        row = list(row) + [None, None]
        t = row[1] or row[0]
        if t and str(t).strip():
            textos.append(str(t))
    wb.close()
    return textos


_SINAL = re.compile(
    r"vazao|medidor|pressao|nivel|hidrom|macromed|calibr|telemetr|"
    r"esgoto|saneamento|adutora|saae|\beta\b|\bete\b"
)


def extra_frases(textos: list[str]) -> list[str]:
    """Bigramas do gabarito que ainda falam do nicho (não 'registro de preços')."""
    bag: dict[str, int] = {}
    for t in textos:
        toks = re.findall(r"[a-z0-9]+", fold(t))
        toks = [x for x in toks if len(x) > 3]
        for a, b in zip(toks, toks[1:]):
            bg = f"{a} {b}"
            if _SINAL.search(bg):
                bag[bg] = bag.get(bg, 0) + 1
    return [k for k, n in bag.items() if n >= 3][:40]


def pontuar(objeto: str, extras: list[str]) -> tuple[int, list[str]]:
    t = fold(objeto)
    if any(re.search(p, t) for p in BLOQUEIO):
        return 0, ["bloqueio"]
    hits = []
    sc = 0
    for p in FORTE:
        if re.search(p, t):
            hits.append(p)
            sc += 3
    if sc == 0:
        return 0, []
    for bg in extras:
        if bg in t:
            hits.append(bg)
            sc += 1
    return sc, hits[:8]


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    s = str(s)[:19]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=TZ)
        except ValueError:
            continue
    return None


def yyyymmdd(d: datetime) -> str:
    return d.strftime("%Y%m%d")


def coletar(corte: datetime, pausa: float, mods: tuple[int, ...]) -> list[dict]:
    hoje = datetime.now(TZ)
    dias = sorted({yyyymmdd(corte), yyyymmdd(hoje)})
    visto: dict[str, dict] = {}
    for dia in dias:
        for mod in mods:
            pagina = 1
            total = 1
            while pagina <= total:
                params = {
                    "dataInicial": dia,
                    "dataFinal": dia,
                    "codigoModalidadeContratacao": mod,
                    "pagina": pagina,
                    "tamanhoPagina": TAMANHO,
                }
                ret = fetch_com_retry(BASE, params)
                if ret is None:
                    print(f"[warn] falha {dia} mod={mod} p={pagina}", file=sys.stderr)
                    break
                dados, total_paginas = ret
                total = int(total_paginas or 1)
                for it in dados or []:
                    key = it.get("numeroControlePNCP")
                    if key:
                        visto[key] = it
                print(
                    f"[coleta] {dia} mod={mod} p={pagina}/{total} +{len(dados or [])}",
                    file=sys.stderr,
                )
                if pagina >= total:
                    break
                pagina += 1
                time.sleep(pausa)
            time.sleep(pausa)
    return list(visto.values())


def enriquece(it: dict, sc: int, hits: list[str], pub: datetime) -> dict:
    u = it.get("unidadeOrgao") or {}
    o = it.get("orgaoEntidade") or {}
    cnpj = o.get("cnpj")
    ano = it.get("anoCompra")
    seq = it.get("sequencialCompra")
    val = it.get("valorTotalEstimado")
    return {
        "score": sc,
        "hits": hits,
        "numero_pncp": it.get("numeroControlePNCP"),
        "data_publicacao": pub.strftime("%Y-%m-%d %H:%M"),
        "data_encerramento": (it.get("dataEncerramentoProposta") or "")[:19],
        "modalidade": it.get("modalidadeNome"),
        "uf": u.get("ufSigla"),
        "municipio": u.get("municipioNome"),
        "orgao": o.get("razaoSocial"),
        "cnpj": cnpj,
        "objeto": re.sub(r"\s+", " ", it.get("objetoCompra") or ""),
        "valor_estimado": val,
        "link_pncp": f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}",
        "link_origem": it.get("linkSistemaOrigem") or "",
    }


def gravar_xlsx(rows: list[dict], path: Path) -> None:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "nicho"
    cols = [
        "score",
        "numero_pncp",
        "data_publicacao",
        "data_encerramento",
        "modalidade",
        "uf",
        "municipio",
        "orgao",
        "cnpj",
        "valor_estimado",
        "objeto",
        "link_pncp",
        "hits",
    ]
    ws.append(cols)
    for r in rows:
        ws.append([", ".join(r["hits"]) if c == "hits" else r.get(c) for c in cols])
    wb.save(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="PNCP 24h filtrado pelo dataset de nicho (tool de agente).")
    ap.add_argument("--dataset", required=True, help="xlsx do gabarito (texto_bruto / x / y)")
    ap.add_argument("--horas", type=int, default=24)
    ap.add_argument("--json", action="store_true", help="stdout JSON (default para agente)")
    ap.add_argument("--xlsx", help="grava planilha além do JSON")
    ap.add_argument("--min-score", type=int, default=3)
    ap.add_argument("--pausa", type=float, default=PAUSA, help="segundos entre páginas")
    ap.add_argument(
        "--mods",
        default=",".join(str(m) for m in MODALIDADES),
        help="códigos de modalidade separados por vírgula (default 6,8,7,4,5,9)",
    )
    args = ap.parse_args()
    mods = tuple(int(x) for x in args.mods.split(",") if x.strip())

    ds = Path(args.dataset).expanduser()
    if not ds.exists():
        print(f"dataset não achado: {ds}", file=sys.stderr)
        return 2

    textos = carregar_dataset(ds)
    extras = extra_frases(textos)
    print(f"[nicho] {len(textos)} textos, {len(extras)} bigramas extra", file=sys.stderr)

    agora = datetime.now(TZ)
    corte = agora - timedelta(hours=args.horas)
    bruto = coletar(corte, args.pausa, mods)

    hits_out = []
    for it in bruto:
        pub = parse_dt(it.get("dataPublicacaoPncp") or it.get("dataInclusao"))
        if not pub or pub < corte:
            continue
        sc, hits = pontuar(it.get("objetoCompra") or "", extras)
        if sc >= args.min_score and hits != ["bloqueio"]:
            hits_out.append(enriquece(it, sc, hits, pub))
    hits_out.sort(key=lambda r: (-r["score"], r["data_publicacao"]), reverse=False)
    hits_out.sort(key=lambda r: -r["score"])

    payload = {
        "corte": corte.isoformat(),
        "coletados": len(bruto),
        "nicho": len(hits_out),
        "dataset": str(ds),
        "itens": hits_out,
    }
    if args.xlsx:
        gravar_xlsx(hits_out, Path(args.xlsx).expanduser())
        print(f"[xlsx] {args.xlsx}", file=sys.stderr)

    # agentes leem stdout; logs vão em stderr
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
