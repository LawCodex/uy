#!/usr/bin/env python3
"""Fetch Uruguayan norms from IMPO's open-data JSON interface (Datos Abiertos: any public norm
URL + ``?json=true``; https://www.impo.com.uy/datos-abiertos/).

robots.txt of www.impo.com.uy sets ``Crawl-Delay: 10``: one request every 10 seconds, single
connection. Responses are cached under $RAW/json/<base>/<nro>-<year>.json (UTF-8).

Usage:
  uy_fetch.py codes                 # constitution + codes + main ordered texts (CODES list)
  uy_fetch.py leyes HIGH LOW        # leyes numbered HIGH down to LOW (year is discovered)
"""
import json
import os
import re
import sys
import time

import requests

RAW = os.environ.get("RAW", "/Users/magicaltux/projects/lawcodex/_raw/uy")
UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
BASE = "https://www.impo.com.uy/bases/"
DELAY = 10.0

# base/number-year of the constitution and codes in IMPO's database
CODES = [
    "constitucion/1967-1967",
    "codigo-civil/16603-1994",
    "codigo-comercio/817-1865",
    "codigo-penal/9155-1933",
    "codigo-general-proceso/15982-1988",
    "codigo-proceso-penal-2017/19293-2014",
    "codigo-tributario/14306-1974",
    "codigo-ninez-adolescencia/17823-2004",
    "codigo-aguas/14859-1978",
    "codigo-rural/10024-1941",
    "codigo-aduanero/19276-2014",
    "codigo-aeronautico/14305-1974",
    "codigo-mineria/15242-1982",
    "codigo-contencioso-administrativo/20333-2024",
    "disposiciones-transitorias-especiales-constitucion/1967-1967",
]

# numbers issued as "decretos-leyes" by the 1973-1985 de facto regime (separate IMPO base)
DL_RANGE = (14068, 15738)

s = requests.Session()
s.headers["User-Agent"] = UA
_last = [0.0]


def polite_get(url):
    for k in range(5):
        wait = DELAY - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = s.get(url, timeout=(30, 600))
            if r.status_code == 200:
                return r.content
            if r.status_code == 404:
                return None
            print("HTTP", r.status_code, url, file=sys.stderr, flush=True)
        except requests.RequestException as e:
            print("ERR", url, e, file=sys.stderr, flush=True)
        time.sleep(30 * (k + 1))
    raise RuntimeError(url)


def decode(raw):
    if raw is None:
        return None
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError:
        txt = raw.decode("latin-1")
    txt = txt.lstrip("﻿ \r\n\t")
    if not txt.startswith("{"):
        return None
    return json.loads(txt, strict=False)


def cache_path(base, key):
    d = os.path.join(RAW, "json", base)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, key + ".json")


def fetch(base, key):
    """Return parsed JSON or None (not found). Cached (also negative results)."""
    p = cache_path(base, key)
    neg = p + ".404"
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    if os.path.exists(neg):
        return None
    data = decode(polite_get(f"{BASE}{base}/{key}?json=true"))
    if data is None:
        open(neg, "w").close()
        return None
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    return data


def year_of(d):
    try:
        return int(d.get("anioNorma"))
    except (TypeError, ValueError):
        return None


def known_years():
    """number -> year from cache (to resume)."""
    out = {}
    for b in ("leyes", "decretos-ley"):
        d = os.path.join(RAW, "json", b)
        if os.path.isdir(d):
            for f in os.listdir(d):
                m = re.match(r"(\d+)-(\d{4})\.json$", f)
                if m:
                    out[int(m.group(1))] = int(m.group(2))
    return out


def leyes(high, low):
    years = known_years()
    year = None
    for n in range(high, low - 1, -1):
        if n in years:
            year = years[n]
            continue
        if year is None:
            near = [years[k] for k in sorted(years) if k > n][:1]
            year = near[0] if near else time.gmtime().tm_year
        found = None
        bases = ("decretos-ley", "leyes") if DL_RANGE[0] <= n <= DL_RANGE[1] else ("leyes",)
        for base in bases:
            for y in (year, year - 1, year + 1, year - 2):
                d = fetch(base, f"{n}-{y}")
                if d is not None:
                    found = y
                    break
            if found:
                break
        if found:
            year = found
            print("ok", n, found, flush=True)
        else:
            print("missing", n, flush=True)


def main():
    if sys.argv[1] == "codes":
        for c in CODES:
            base, key = c.split("/")
            d = fetch(base, key)
            print(c, "ok" if d else "NOT FOUND", flush=True)
    elif sys.argv[1] == "leyes":
        leyes(int(sys.argv[2]), int(sys.argv[3]))


if __name__ == "__main__":
    main()
