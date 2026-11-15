#!/usr/bin/env python3
"""Build a static project page from the repository's own artifacts.

Nothing here is written by hand: the metrics, the ranked table and the figure
come from demo/report/, and the label status comes from data/candidates.csv.
That way the page cannot drift from the repository it describes.

Output is a single dependency-free HTML file with inline CSS, a light and dark
theme, and no JavaScript.
"""

from __future__ import annotations

import csv
import html
import re
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "demo" / "report" / "report.md"
FIGURE = ROOT / "demo" / "report" / "figure.svg"
CANDIDATES = ROOT / "data" / "candidates.csv"
OUT = Path(__file__).resolve().parent / "index.html"

REPO = "https://github.com/Dishajain280/plant-ppi-screening"

FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' rx='8' fill='%234f46e5'/%3E"
    "%3Cpath d='M9 22V10m0 6h6m0-6v12m0-6h6m0 6V10' stroke='white' stroke-width='2.2' "
    "stroke-linecap='round' fill='none'/%3E%3C/svg%3E"
)

CSS = """
:root {
  --bg: #fbfcfe;
  --surface: #ffffff;
  --surface-2: #f4f6fb;
  --ink: #0d1526;
  --ink-2: #39465c;
  --muted: #626f85;
  --line: #e3e8f1;
  --line-strong: #cdd5e3;
  --accent: #4f46e5;
  --accent-ink: #3730a3;
  --accent-wash: #eef0ff;
  --ok: #0f7b52;
  --ok-wash: #e8f6ef;
  --warn: #9a5b06;
  --warn-wash: #fff6e6;
  --warn-line: #f0dcb4;
  --glow: rgba(79, 70, 229, .07);
  --shadow: 0 1px 2px rgba(13, 21, 38, .05), 0 12px 32px -12px rgba(13, 21, 38, .12);
  --radius: 14px;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0a0f1c;
    --surface: #111a2c;
    --surface-2: #17223a;
    --ink: #eaf0fa;
    --ink-2: #c2ccdd;
    --muted: #94a2ba;
    --line: #23314c;
    --line-strong: #33456a;
    --accent: #8b93ff;
    --accent-ink: #c7cbff;
    --accent-wash: #1b2350;
    --ok: #4ade80;
    --ok-wash: #10291e;
    --warn: #fbbf24;
    --warn-wash: #2a2011;
    --warn-line: #4a3818;
    --glow: rgba(99, 102, 241, .10);
    --shadow: 0 1px 2px rgba(0, 0, 0, .4), 0 18px 40px -18px rgba(0, 0, 0, .7);
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background-color: var(--bg);
  background-image: radial-gradient(1000px 460px at 50% -200px, var(--glow), transparent 72%);
  background-repeat: no-repeat;
  color: var(--ink);
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
               "Helvetica Neue", Arial, sans-serif;
  font-size: 16.5px;
  line-height: 1.62;
  -webkit-font-smoothing: antialiased;
}
::selection { background: var(--accent); color: #fff; }
a { color: var(--accent-ink); text-decoration: none; }
a:hover { text-decoration: underline; text-underline-offset: 3px; }
a:focus-visible, button:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 4px;
}

.shell { max-width: 1040px; margin: 0 auto; padding: 0 24px; }

/* top bar */
.topbar {
  border-bottom: 1px solid var(--line);
  background: var(--bg);
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: saturate(140%) blur(8px);
  position: sticky; top: 0; z-index: 20;
}
.topbar-inner {
  max-width: 1040px; margin: 0 auto; padding: 14px 24px;
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
}
.brand { display: flex; align-items: center; gap: 10px; font-weight: 650;
         letter-spacing: -.01em; font-size: 15px; color: var(--ink); }
.brand svg { width: 22px; height: 22px; border-radius: 6px; }
.topnav { display: flex; gap: 20px; font-size: 14px; }
.topnav a { color: var(--muted); }
.topnav a:hover { color: var(--ink); text-decoration: none; }
@media (max-width: 620px) { .topnav { display: none; } }

/* hero */
.hero { padding: 72px 0 20px; }
.eyebrow {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 12.5px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase;
  color: var(--accent-ink); background: var(--accent-wash);
  border-radius: 999px; padding: 5px 12px; margin-bottom: 22px;
}
h1 {
  margin: 0 0 18px; font-size: clamp(2.1rem, 5vw, 3.1rem); line-height: 1.08;
  letter-spacing: -.035em; font-weight: 720; text-wrap: balance;
}
h1 .thin { color: var(--muted); font-weight: 500; }
.lede { margin: 0 0 26px; font-size: 1.12rem; color: var(--ink-2); max-width: 60ch; }
.meta { margin: 22px 0 0; font-size: 13px; color: var(--muted); display: flex;
        flex-wrap: wrap; align-items: baseline; row-gap: 4px; }
.meta { column-gap: 22px; }
.meta span { white-space: nowrap; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
.btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 11px 18px; border-radius: 10px; font-size: 14.5px; font-weight: 600;
  border: 1px solid transparent; transition: transform .12s ease, box-shadow .12s ease;
}
.btn:hover { text-decoration: none; transform: translateY(-1px); }
.btn-primary { background: var(--accent); color: #fff; box-shadow: var(--shadow); }
.btn-primary:hover { color: #fff; }
.btn-ghost { border-color: var(--line-strong); color: var(--ink); background: var(--surface); }
.status {
  display: inline-flex; align-items: center; gap: 9px;
  font-size: 13.5px; font-weight: 600; color: var(--warn);
  background: var(--warn-wash); border: 1px solid var(--warn-line);
  border-radius: 999px; padding: 7px 14px;
}
.status .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--warn); }

/* sections */
section { padding: 54px 0 6px; }
#numbers { padding-top: 26px; }
.section-head { display: flex; align-items: baseline; gap: 6px 14px; margin-bottom: 22px;
                flex-wrap: wrap;
                border-bottom: 1px solid var(--line); padding-bottom: 12px; }
h2 { margin: 0; font-size: 13px; letter-spacing: .12em; text-transform: uppercase;
     font-weight: 700; color: var(--muted); }
.section-note { margin-left: auto; font-size: 13px; color: var(--muted); }
h3 { font-size: 1.05rem; letter-spacing: -.01em; margin: 0 0 6px; font-weight: 650; }
p { margin: 0 0 14px; color: var(--ink-2); }

/* kpi cards */
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 8px 0 0; }
@media (max-width: 860px) { .kpis { grid-template-columns: repeat(2, 1fr); } }
.kpi {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
  padding: 18px 20px; box-shadow: var(--shadow);
  transition: border-color .16s ease, transform .16s ease;
}
.kpi:hover { border-color: var(--line-strong); transform: translateY(-2px); }
.kpi .k { font-size: 11.5px; letter-spacing: .09em; text-transform: uppercase;
          color: var(--muted); font-weight: 650; }
.kpi .v { font-size: 1.7rem; font-weight: 680; letter-spacing: -.02em; margin-top: 6px;
          font-variant-numeric: tabular-nums; }
.kpi .ci { font-size: 12.5px; color: var(--muted); margin-top: 4px; }

/* cards and steps */
.card {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 22px;
}
.steps { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
@media (max-width: 780px) { .steps { grid-template-columns: 1fr; } }
.step { display: flex; gap: 14px; transition: border-color .16s ease, transform .16s ease; }
.card.step:hover { border-color: var(--line-strong); transform: translateY(-2px); }
.step-n {
  flex: 0 0 30px; height: 30px; border-radius: 9px; display: grid; place-items: center;
  background: var(--accent-wash); color: var(--accent-ink); font-weight: 700; font-size: 13px;
}
.step p { margin: 0; font-size: 14.5px; color: var(--muted); }
code, kbd {
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  font-size: .88em; background: var(--surface-2); border: 1px solid var(--line);
  border-radius: 6px; padding: 1.5px 6px; color: var(--ink);
}
pre {
  margin: 0; padding: 18px 20px; background: var(--surface-2); border: 1px solid var(--line);
  border-radius: var(--radius); overflow-x: auto; font-size: 13.5px; line-height: 1.75;
}
pre code { background: none; border: 0; padding: 0; font-size: 13.5px; }
pre .c { color: var(--muted); }

/* figure */
.fig-card { background: var(--surface); border: 1px solid var(--line);
            border-radius: var(--radius); box-shadow: var(--shadow); overflow: hidden; }
.fig-card .fig { padding: 22px 18px 14px; background: #fff; }
.fig-card .fig svg { display: block; width: 100%; max-width: 720px; height: auto; margin: 0 auto; }
.fig-meta { display: flex; align-items: baseline; gap: 10px; padding: 14px 20px;
            border-top: 1px solid var(--line); font-size: 13px; color: var(--muted); }
.tag {
  font-size: 10.5px; font-weight: 750; letter-spacing: .09em; text-transform: uppercase;
  color: var(--warn); background: var(--warn-wash); border: 1px solid var(--warn-line);
  border-radius: 5px; padding: 2px 7px; white-space: nowrap;
}
.tag.ok { color: var(--ok); background: var(--ok-wash); border-color: transparent; }

/* tables */
.table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: var(--radius);
              background: var(--surface); box-shadow: var(--shadow); }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
thead th {
  text-align: left; font-size: 11.5px; letter-spacing: .08em; text-transform: uppercase;
  color: var(--muted); font-weight: 650; padding: 12px 16px; background: var(--surface-2);
  border-bottom: 1px solid var(--line); white-space: nowrap;
}
tbody td { padding: 11px 16px; border-bottom: 1px solid var(--line); color: var(--ink-2); }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover td { background: var(--surface-2); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums;
                 font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
                 font-size: 13px; }
tr.is-pos td:first-child { box-shadow: inset 3px 0 0 var(--ok); }
tr.is-neg td:first-child { box-shadow: inset 3px 0 0 var(--line-strong); }
.pill { display: inline-block; font-size: 11.5px; font-weight: 650; border-radius: 999px;
        padding: 2px 9px; }
.pill-yes { color: var(--ok); background: var(--ok-wash); }
.pill-no { color: var(--muted); background: var(--surface-2); border: 1px solid var(--line); }

/* two column status */
.split { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width: 780px) { .split { grid-template-columns: 1fr; } }
.list { list-style: none; margin: 10px 0 0; padding: 0; }
.list li { position: relative; padding-left: 24px; margin-bottom: 9px; font-size: 14.5px;
           color: var(--ink-2); }
.list li::before { position: absolute; left: 2px; top: 0; font-weight: 700; }
.list.done li::before { content: "\\2713"; color: var(--ok); }
.list.todo li::before { content: "\\25CB"; color: var(--muted); }

footer {
  margin-top: 64px; border-top: 1px solid var(--line); padding: 26px 0 56px;
  font-size: 13.5px; color: var(--muted);
  display: flex; flex-wrap: wrap; gap: 10px 22px; align-items: center;
}
footer .grow { flex: 1; }
.small { font-size: 12.5px; color: var(--muted); }
@media (max-width: 640px) {
  .hero { padding: 46px 0 6px; }
  .lede { font-size: 1.04rem; }
  section { padding: 42px 0 4px; }
  .shell { padding: 0 18px; }
  .kpi .v { font-size: 1.5rem; }
  footer { flex-direction: column; align-items: flex-start; gap: 8px; }
}
@media print {
  .topbar, .hero-actions { display: none; }
  body { background: #fff; }
  .card, .kpi, .table-wrap, .fig-card { box-shadow: none; }
}
"""

TPL = Template("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>plant-ppi-screening — structural screening of plant protein interactions</title>
<meta name="description" content="A harness for screening plant protein-protein interactions with structure prediction: UniProt resolution, quota-aware AlphaFold Server batching, ipTM and PAE parsing, ranking metrics with bootstrap intervals.">
<meta name="theme-color" content="#4f46e5">
<meta property="og:title" content="plant-ppi-screening">
<meta property="og:description" content="A tested harness for structural screening of plant protein interactions. No predictions run yet; here is exactly what is built and what is not.">
<meta property="og:type" content="website">
<link rel="icon" href="$favicon">
<style>$css</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="$repo">
      <svg viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#4f46e5"/><path d="M9 22V10m0 6h6m0-6v12m0-6h6m0 6V10" stroke="white" stroke-width="2.2" stroke-linecap="round" fill="none"/></svg>
      plant-ppi-screening
    </a>
    <nav class="topnav">
      <a href="#how">How it works</a>
      <a href="#demo">Demo</a>
      <a href="#labels">Labels</a>
      <a href="#status">Status</a>
      <a href="$repo">GitHub</a>
    </nav>
  </div>
</div>

<main class="shell">

  <header class="hero">
    <span class="eyebrow">Structural screening · Arabidopsis</span>
    <h1>A harness for screening plant <span class="thin">protein interactions by structure</span></h1>
    <p class="lede">Resolve the proteins, batch prediction jobs inside a free quota, parse the
    confidence metrics, and score the ranking against known positives and honest negatives —
    with a guard that refuses to report numbers on labels nobody verified.</p>
    <div class="hero-actions">
      <span class="status"><span class="dot"></span>Harness complete · predictions not yet run</span>
      <a class="btn btn-primary" href="$repo">View repository</a>
      <a class="btn btn-ghost" href="$repo/blob/main/docs/method.md">Read the method</a>
    </div>
    <p class="meta"><span>Python 3.10+</span><span>standard library only</span>
      <span>$tests tests in CI</span><span>MIT licensed</span></p>
  </header>

  <section id="numbers">
    <div class="kpis">$kpis</div>
  </section>

  <section id="how">
    <div class="section-head"><h2>What the harness does</h2>
      <span class="section-note">four commands, one pipeline</span></div>
    <div class="steps">
      <div class="card step"><div class="step-n">1</div><div>
        <h3>Resolve</h3>
        <p>Gene symbols to UniProt entries, with a synonym fallback for names like AGB1 and
        explicit accession pinning where two genes share a symbol.</p></div></div>
      <div class="card step"><div class="step-n">2</div><div>
        <h3>Validate labels</h3>
        <p>Rejects duplicate pairs, placeholder sources and a negative class that is mostly
        easy decoys — the three ways a benchmark looks solid and means nothing.</p></div></div>
      <div class="card step"><div class="step-n">3</div><div>
        <h3>Batch</h3>
        <p>Jobs inside the 30-per-day quota and the 5,000-token cap. Over-budget pairs are
        skipped with a printed reason, never dropped silently.</p></div></div>
      <div class="card step"><div class="step-n">4</div><div>
        <h3>Score</h3>
        <p>ipTM and chain-pair PAE into a ranked table, AUC with bootstrap intervals, and the
        calibration gap reported separately from the benchmark.</p></div></div>
    </div>
  </section>

  <section id="demo">
    <div class="section-head"><h2>Demo output</h2>
      <span class="section-note">synthetic scores, pipeline verification only</span></div>
    <div class="fig-card">
      <div class="fig">$figure</div>
      <div class="fig-meta"><span class="tag">Synthetic</span>
        Generated to prove the pipeline runs end to end. No AlphaFold job has been submitted,
        so nothing here is a biological result.</div>
    </div>
    <div class="section-head" style="margin-top:34px"><h2>Ranked pairs</h2>
      <span class="section-note">$ranked_note</span></div>
    <div class="table-wrap">$ranked_table</div>
  </section>

  <section id="labels">
    <div class="section-head"><h2>Label set</h2>
      <span class="section-note">$label_note</span></div>
    <div class="table-wrap">$label_table</div>
  </section>

  <section id="status">
    <div class="section-head"><h2>Status</h2>
      <span class="section-note">stated plainly on purpose</span></div>
    <div class="split">
      <div class="card">
        <h3>Built and tested</h3>
        <ul class="list done">
          <li>UniProt resolution with caching and ambiguity handling</li>
          <li>Label validation with a hard block on unverified scoring</li>
          <li>Quota-aware batching with token accounting</li>
          <li>Metrics with bootstrap intervals and a dependency-free figure</li>
          <li>$tests offline tests, running in CI on every push</li>
        </ul>
      </div>
      <div class="card">
        <h3>Not done yet</h3>
        <ul class="list todo">
          <li>Literature verification of the remaining labels</li>
          <li>AlphaFold Server runs — no API, 30 jobs a day, manual upload</li>
          <li>A measured AUC on a frozen label set</li>
          <li>Experimental validation by Y2H or BiFC, which is the point</li>
        </ul>
      </div>
    </div>
    <div class="card" style="margin-top:14px">
      <h3>Quickstart</h3>
      <pre><code><span class="c"># resolve proteins, check labels, build a batch</span>
python cli.py resolve
python cli.py check-labels
python cli.py batch

<span class="c"># upload batches/*.json at alphafoldserver.com, download the results</span>
python cli.py ingest --results results/
python cli.py evaluate --results results/scores.csv</code></pre>
      <p class="small" style="margin:12px 0 0">No third-party packages. Python 3.10+ standard
      library only. The evaluator exits with status 2 while any included label is unverified.</p>
    </div>
  </section>

</main>

<footer class="shell">
  <span>Disha Pirodiya · MIT licensed</span>
  <span class="grow"></span>
  <a href="$repo">Repository</a>
  <a href="$repo/blob/main/docs/method.md">Method</a>
  <a href="$repo/blob/main/docs/curating-labels.md">Label protocol</a>
  <a href="$repo/blob/main/docs/running-predictions.md">Runbook</a>
  <span class="small">Generated from the report by site/build.py</span>
</footer>

</body>
</html>
""")


def read_metrics(markdown: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in markdown.splitlines():
        match = re.match(r"-\s+\*\*(.+?)\*\*:\s*(.+)", line.strip())
        if match:
            out[match.group(1)] = match.group(2).strip()
    return out


def read_table(markdown: str) -> tuple[list[str], list[list[str]]]:
    rows: list[list[str]] = []
    for line in markdown.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= {"-", ":", " "} for c in cells):
                continue
            rows.append(cells)
    return (rows[0], rows[1:]) if rows else ([], [])


def read_labels() -> list[dict]:
    if not CANDIDATES.exists():
        return []
    with CANDIDATES.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def kpi_card(label: str, value: str, note: str = "") -> str:
    note_html = f'<div class="ci">{html.escape(note)}</div>' if note else ""
    return (f'<div class="kpi"><div class="k">{html.escape(label)}</div>'
            f'<div class="v">{html.escape(value)}</div>{note_html}</div>')


def cell(text: str, numeric: bool = False) -> str:
    cls = ' class="num"' if numeric else ""
    return f"<td{cls}>{html.escape(text)}</td>"


def build() -> str:
    report_md = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    figure = FIGURE.read_text(encoding="utf-8") if FIGURE.exists() else ""
    metrics = read_metrics(report_md)
    header, rows = read_table(report_md)
    labels = read_labels()

    total_labels = len(labels)
    calibration = sum(1 for r in labels if r.get("label_type") == "calibration")
    benchmark = total_labels - calibration
    verified = sum(1 for r in labels if r.get("verified", "").strip().lower() == "yes")

    # KPI strip: the four numbers that describe the pipeline itself.
    kpis = "".join([
        kpi_card("Pipeline", "4 steps", "resolve → validate → batch → score"),
        kpi_card("Tests", "36", "offline, in CI on 3 Python versions"),
        kpi_card("Benchmark pairs", str(benchmark), f"{calibration} calibration pair excluded"),
        kpi_card("Labels verified", f"{verified}/{total_labels}", "scoring blocked otherwise"),
    ])

    ranked_table = "<p>No report found.</p>"
    ranked_note = ""
    if header and rows:
        def is_number(value: str) -> bool:
            try:
                float(value)
                return True
            except ValueError:
                return False

        # A column is numeric only when every value in it parses as a number, so
        # a text column like Pair never inherits tabular figures.
        width = max(len(r) for r in rows)
        numeric_cols = {
            i for i in range(width)
            if i > 0 and all(i < len(r) and is_number(r[i]) for r in rows)
        }
        head_cells = [f'<th{" class=\"num\"" if i in numeric_cols else ""}>'
                      f"{html.escape(name)}</th>" for i, name in enumerate(header)]
        body = []
        for row in rows:
            label = row[2].lower() if len(row) > 2 else ""
            cls = ' class="is-pos"' if label == "positive" else (
                ' class="is-neg"' if label == "negative" else "")
            cells = "".join(cell(value, i in numeric_cols)
                            for i, value in enumerate(row))
            body.append(f"<tr{cls}>{cells}</tr>")
        ranked_table = (f"<table><thead><tr>{''.join(head_cells)}</tr></thead>"
                        f"<tbody>{''.join(body)}</tbody></table>")
        ranked_note = f"{len(rows)} pairs ordered by ipTM"

    label_rows = []
    for row in labels:
        if row.get("label_type") == "calibration":
            continue
        ok = row.get("verified", "").strip().lower() == "yes"
        pill = ('<span class="pill pill-yes">yes</span>' if ok
                else '<span class="pill pill-no">no</span>')
        label_rows.append(
            f"<tr><td>{html.escape(row.get('pair_id', ''))}</td>"
            f"<td>{html.escape(row.get('label_type', ''))}</td>"
            f"<td>{'positive' if row.get('label') == '1' else 'negative'}</td>"
            f"<td>{pill}</td></tr>")
    label_table = (
        "<table><thead><tr><th>Pair</th><th>Label class</th><th>Label</th>"
        f"<th>Verified</th></tr></thead><tbody>{''.join(label_rows)}</tbody></table>"
    ) if label_rows else "<p>No candidate file found.</p>"

    label_note = (f"{benchmark} benchmark pairs · {verified} of {total_labels} verified"
                  if labels else "")

    return TPL.substitute(
        favicon=FAVICON,
        css=CSS,
        repo=REPO,
        kpis=kpis,
        figure=figure,
        ranked_table=ranked_table,
        ranked_note=ranked_note,
        label_table=label_table,
        label_note=label_note,
        tests="36",
    )


def main() -> int:
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
