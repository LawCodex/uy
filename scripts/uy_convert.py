#!/usr/bin/env python3
"""Convert IMPO JSON (cached by uy_fetch.py) to Markdown.

constitucion/ codigos/ leyes/<year>/ley-<n>.md
"""
import html
import json
import os
import re
import sys
import unicodedata
from datetime import date

import yaml

RAW = os.environ.get("RAW", "/Users/magicaltux/projects/lawcodex/_raw/uy")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.impo.com.uy"
TODAY = date.today().isoformat()

RANK = {"PARTE": 1, "LIBRO": 2, "SECCION": 3, "TITULO": 4, "CAPITULO": 5, "SUBCAPITULO": 6}


def plain(s):
    s = re.sub(r"(?i)<br\s*/?>", "\n", s or "")
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).replace("\r\n", "\n").replace("\r", "\n")


def kind_of(h):
    k = unicodedata.normalize("NFKD", h.split(" ")[0].upper()).encode("ascii", "ignore").decode()
    return k if k in RANK else None


def paragraphs(txt):
    """IMPO texts are hard-wrapped at ~75 chars; a paragraph starts with an indented line."""
    txt = plain(txt).replace("\r\n", "\n").replace("\r", "\n")
    out, cur = [], []
    for line in txt.split("\n"):
        if not line.strip():
            if cur:
                out.append(" ".join(cur))
                cur = []
            continue
        if re.match(r"^\s{2,}\S", line) and cur:
            out.append(" ".join(cur))
            cur = []
        cur.append(line.strip())
    if cur:
        out.append(" ".join(cur))
    return [re.sub(r"\s{2,}", " ", p).strip() for p in out if p.strip()]


def esc(p):
    # avoid accidental Markdown headings / list renumbering at paragraph start
    if re.match(r"^(#|\d+\.\s)", p):
        p = "\\" + p
    return p


def dmy(s):
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def convert(d, base, key, title, typ, url):
    arts = d.get("articulos", [])
    heads = []
    for a in arts:
        for h in plain(a.get("titulosArticulo", "")).split("\n"):
            k = kind_of(h.strip())
            if k:
                heads.append(k)
    used = sorted({RANK[k] for k in heads})
    lvl = {r: min(2 + i, 5) for i, r in enumerate(used)}
    body = []
    vistos = plain(d.get("vistos", "")).strip()
    if vistos:
        body += [esc(p) for p in paragraphs(d["vistos"])]
    for a in arts:
        for h in plain(a.get("titulosArticulo", "")).split("\n"):
            h = re.sub(r"\s+", " ", h).strip()
            if not h:
                continue
            k = kind_of(h)
            body.append("#" * (lvl[RANK[k]] if k else 5) + " " + h)
        label = (a.get("tituloArticulo") or ("Artículo " + a.get("nroArticulo", ""))).strip()
        body.append("###### " + re.sub(r"\s+", " ", label))
        body += [esc(p) for p in paragraphs(a.get("textoArticulo", ""))]
        notes = plain(a.get("notasArticulo", "")).strip()
        if notes:
            body.append("\n".join("> " + re.sub(r"\s+", " ", l).strip() for l in notes.split("\n") if l.strip()))
    front = {
        "title": title,
        "identifier": " ".join(x for x in [(d.get("tipoNorma") or "").strip(), "/".join(str(v) for v in (d.get("nroNorma"), d.get("anioNorma")) if v)] if x),
        "type": typ, "jurisdiction": "uy", "language": "es",
        "date": dmy(d.get("fechaPromulgacion")) or dmy(d.get("fechaPublicacion")),
        "published": dmy(d.get("fechaPublicacion")),
        "status": "in_force" if "Actualizado" in (d.get("leyenda") or "") else "unknown",
        "source": url, "retrieved": TODAY,
    }
    leyenda = (d.get("leyenda") or "").strip()
    pre = []
    if leyenda:
        pre.append(f"> IMPO: {leyenda}.")
    refs = plain(d.get("referenciasNorma", "")).strip()
    if refs:
        pre.append("> " + re.sub(r"\s+", " ", refs))
    fm = yaml.safe_dump(front, allow_unicode=True, sort_keys=False, width=1000).strip()
    return "\n".join(["---", fm, "---", "", f"# {title}", ""] + ([("\n>\n".join(pre)), ""] if pre else [])
                     + ["\n\n".join(body), ""])


CODE_TITLES = {}


def main():
    jdir = os.path.join(RAW, "json")
    n = 0
    for base in sorted(os.listdir(jdir)):
        for f in sorted(os.listdir(os.path.join(jdir, base))):
            if not f.endswith(".json"):
                continue
            key = f[:-5]
            d = json.load(open(os.path.join(jdir, base, f), encoding="utf-8"))
            url = f"{SITE}/bases/{base}/{key}"
            if base == "leyes":
                num, year = key.split("-")
                title = f"Ley N° {int(num):,}".replace(",", ".") + " — " + (d.get("nombreNorma") or "").strip()
                out = os.path.join(REPO, "leyes", year, f"ley-{num}.md")
                typ = "act"
            elif base == "decretos-ley":
                num, year = key.split("-")
                title = f"Decreto Ley N° {int(num):,}".replace(",", ".") + " — " + (d.get("nombreNorma") or "").strip()
                out = os.path.join(REPO, "decretos-ley", year, f"decreto-ley-{num}.md")
                typ = "decree-law"
            elif base == "constitucion":
                title = "Constitución de la República Oriental del Uruguay"
                out = os.path.join(REPO, "constitucion", "constitucion-1967.md")
                typ = "constitution"
            elif base.startswith("disposiciones-transitorias"):
                title = "Disposiciones Transitorias y Especiales de la Constitución de la República"
                out = os.path.join(REPO, "constitucion", "disposiciones-transitorias-y-especiales.md")
                typ = "constitution"
            else:
                title = (d.get("tipoNorma") or base).strip()
                if title.isupper():
                    title = title.title()
                out = os.path.join(REPO, "codigos", f"{base}.md")
                typ = "code"
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "w", encoding="utf-8").write(convert(d, base, key, title, typ, url).replace("\r", ""))
            n += 1
    print("written", n)


if __name__ == "__main__":
    main()
