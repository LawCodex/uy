# LawCodex — Uruguay (uy)

Uruguayan legislation as Markdown, from the **IMPO** (Dirección Nacional de Impresiones y
Publicaciones Oficiales) normative database, through its **open-data JSON interface**: the
**Constitución de la República (1967, updated)** with its transitional provisions, the
**national codes** (current, updated texts) and **laws** (leyes), newest first.

Part of [LawCodex](https://github.com/LawCodex): one public repository per jurisdiction.

Retrieved: **2026-10-13** (laws are added progressively, see below). Language: Spanish (`es`).

Status: **partial** — constitution and codes complete; laws only for the most recent years.

## What is covered

| Category | Directory | Files |
|---|---|---|
| Constitución de la República (1967, with the 1989, 1994, 1996 and 2004 reforms) and its Disposiciones Transitorias y Especiales | `constitucion/` | 2 |
| Codes (updated texts) | `codigos/` | 13 |
| Laws (leyes), number range 18.469–20.530 | `leyes/<year>/ley-<n>.md` | 2,059 |

Codes: Código Civil, Código de Comercio, Código Penal, Código General del Proceso, Código del
Proceso Penal (2017), Código Tributario, Código de la Niñez y la Adolescencia, Código de Aguas,
Código Rural, Código Aduanero, Código Aeronáutico, Código de Minería, Código de lo Contencioso
Administrativo (2024).

Each file reproduces IMPO's text article by article: the division headings (SECCIÓN, CAPÍTULO,
LIBRO, TÍTULO…) as headings, each article as a `######` heading, and IMPO's editorial notes
for the article (wording history: *"Redacción dada por…"*, cross references) as a quote block
below it. Texts marked by IMPO as *Documento Actualizado* carry the current (consolidated)
wording.

## What is NOT covered

- **Older laws.** IMPO's robots.txt sets `Crawl-Delay: 10`; with one request every 10 seconds
  (and large JSON documents) only ~100 laws per hour can be fetched, so the corpus of ~20,500
  laws could not be fetched in this run. Laws are fetched from the newest number downwards;
  the range covered is given in the table above. Re-running `scripts/uy_fetch.py leyes HIGH LOW`
  continues the job (cached documents are not re-downloaded).
- The Parlamento's open-data list of promulgated laws (parlamento.gub.uy) answered HTTP 403.
- Decrees, resolutions and other secondary norms (also in IMPO's database).

## Sources

- IMPO — Datos Abiertos: https://www.impo.com.uy/datos-abiertos/ — every public norm URL with
  `?json=true` returns the norm as JSON (schema: http://www.impo.com.uy/resources/basesIMPO.json).
  Each file's `source` is the norm's IMPO URL.

## Licence

IMPO publishes its database as open data under the **Licencia de Datos Abiertos – Uruguay**
(Decreto 54/017; https://www.impo.com.uy/wp_impo/wp-content/uploads/2018/06/licencia-de-datos-abiertos.pdf),
which allows reuse with attribution (source: IMPO). Note that IMPO's older "Condiciones
Generales de Uso" of the Banco de Datos (subscription era) restrict copying; the open-data
licence announced on the Datos Abiertos page (since July 2018) is the one relied on here.

## Structure

```
constitucion/constitucion-1967.md
constitucion/disposiciones-transitorias-y-especiales.md
codigos/<impo-base>.md                     e.g. codigo-civil.md
leyes/<year>/ley-<number>.md
decretos-ley/<year>/decreto-ley-<number>.md
```

Front matter: `identifier` = IMPO type + number/year; `date` = promulgation, `published` =
publication in the Diario Oficial; `status` = `in_force` when IMPO marks the document as
"Documento Actualizado".

## Regenerate

```
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
RAW=/path/to/scratch .venv/bin/python scripts/uy_fetch.py codes
RAW=/path/to/scratch .venv/bin/python scripts/uy_fetch.py leyes 20540 9000   # slow: 10 s crawl delay
RAW=/path/to/scratch .venv/bin/python scripts/uy_convert.py
```
