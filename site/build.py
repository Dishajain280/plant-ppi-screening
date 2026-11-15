#!/usr/bin/env python3
"""Build a static project page from the repository's own artifacts.

Nothing here is written by hand: the metrics, the ranked table and the figure
come from demo/report/, and the label status comes from data/candidates.csv.
That way the page cannot drift from the repository it describes.
"""

from __future__ import annotations

import csv
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "demo" / "report" / "report.md"
FIGURE = ROOT / "demo" / "report" / "figure.svg"
CANDIDATES = ROOT / "data" / "candidates.csv"
OUT = Path(__file__).resolve().parent / "index.html"

REPO = "https://github.com/Dishajain280/plant-ppi-screening"


def read_metrics(markdown: str) -> list[tuple[str, str]]:
    """Pull the '- **name**: value' bullets out of the report."""
    out = []
    for line in markdown.splitlines():
        match = re.match(r"-\s+\*\*(.+?)\*\*:\s*(.+)", line.strip())
        if match:
            out.append((match.group(1), match.group(2).strip()))
    return out


def read_table(markdown: str) -> tuple[list[str], list[list[str]]]:
    """Pull the first pipe table out of the report."""
    rows: list[list[str]] = []
    for line in markdown.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= {"-", ":", " "} for c in cells):
                continue  # separator row
            rows.append(cells)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def read_labels() -> list[dict]:
    if not CANDIDATES.exists():
        return []
    with CANDIDATES.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build() -> str:
    report_md = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    figure = FIGURE.read_text(encoding="utf-8") if FIGURE.exists() else ""
    metrics = read_metrics(report_md)
    header, rows = read_table(report_md)
    labels = read_labels()

    verified = sum(1 for r in labels if r.get("verified", "").strip().lower() == "yes")
    calibration = sum(1 for r in labels if r.get("label_type") == "calibration")
    benchmark = len(labels) - calibration

    metric_html = "\n".join(
        f'<div class="metric"><span class="metric-name">{html.escape(n)}</span>'
        f'<span class="metric-value">{html.escape(v)}</span></div>'
        for n, v in metrics
    )

    table_html = ""
    if header and rows:
        head = "".join(f"<th>{html.escape(c)}</th>" for c in header)
        body = "".join(
            "<tr>" + "".join(
                f'<td class="{"num" if c.replace(".", "").replace("-", "").isdigit() else ""}">'
                f"{html.escape(c)}</td>" for c in row
            ) + "</tr>"
            for row in rows
        )
        table_html = f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    label_rows = "".join(
        f"<tr><td>{html.escape(r.get('pair_id', ''))}</td>"
        f"<td>{html.escape(r.get('label_type', ''))}</td>"
        f"<td>{'yes' if r.get('verified', '').strip().lower() == 'yes' else 'no'}</td></tr>"
        for r in labels
        if r.get("label_type") != "calibration"
    )
    label_html = (
        "<table><thead><tr><th>Pair</th><th>Label class</th><th>Verified</th></tr></thead>"
        f"<tbody>{label_rows}</tbody></table>"
    ) if labels else "<p>No candidate file found.</p>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>plant-ppi-screening — structural screening harness</title>
<meta name="description" content="A harness for screening plant protein-protein interactions with structure prediction: batching, confidence parsing and ranking metrics.">
<style>
  :root {{ --ink:#1f2328; --muted:#59636e; --line:#d8dee4; --wash:#f6f8fa;
           --green:#1a7f37; --amber:#9a6700; --amber-wash:#fff8e5; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:#fff; color:var(--ink);
          font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
          line-height:1.55; font-size:16px; }}
  .wrap {{ max-width:880px; margin:0 auto; padding:56px 24px 80px; }}
  header h1 {{ font-size:30px; letter-spacing:-0.02em; margin:0 0 10px; }}
  .lede {{ font-size:17px; color:var(--muted); margin:0 0 18px; max-width:62ch; }}
  .pill {{ display:inline-block; background:var(--amber-wash); color:var(--amber);
           border:1px solid #e6d5a8; border-radius:999px; padding:4px 12px;
           font-size:13px; font-weight:600; }}
  nav {{ margin-top:18px; font-size:14px; }}
  nav a {{ color:#0b5cad; text-decoration:none; margin-right:16px; }}
  nav a:hover {{ text-decoration:underline; }}
  h2 {{ font-size:14px; letter-spacing:0.08em; text-transform:uppercase; color:var(--muted);
        margin:44px 0 12px; padding-bottom:6px; border-bottom:1px solid var(--line); }}
  p {{ margin:0 0 12px; }}
  ol, ul {{ margin:0 0 12px; padding-left:20px; }}
  li {{ margin-bottom:6px; }}
  code {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-size:13.5px;
          background:var(--wash); padding:1px 5px; border-radius:4px; }}
  .fig {{ border:1px solid var(--line); border-radius:8px; padding:8px; background:#fff;
          overflow-x:auto; }}
  .fig svg {{ display:block; width:100%; height:auto; }}
  .tag {{ font-size:11px; font-weight:700; letter-spacing:0.04em; text-transform:uppercase;
          color:var(--amber); background:var(--amber-wash); border-radius:4px;
          padding:2px 7px; margin-left:8px; vertical-align:middle; }}
  .metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
              gap:10px; margin:14px 0 18px; }}
  .metric {{ border:1px solid var(--line); border-radius:8px; padding:10px 12px;
             background:var(--wash); }}
  .metric-name {{ display:block; font-size:12px; text-transform:uppercase;
                  letter-spacing:0.05em; color:var(--muted); }}
  .metric-value {{ display:block; font-size:20px; font-weight:600;
                   font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
  table {{ width:100%; border-collapse:collapse; font-size:14px; margin:8px 0 4px; }}
  th {{ text-align:left; font-size:12px; text-transform:uppercase; letter-spacing:0.04em;
        color:var(--muted); border-bottom:1px solid var(--line); padding:8px 10px; }}
  td {{ border-bottom:1px solid var(--wash); padding:8px 10px; }}
  td.num {{ text-align:right; font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
  tbody tr:hover {{ background:var(--wash); }}
  .note {{ font-size:13.5px; color:var(--muted); }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
  @media (max-width:640px) {{ .grid {{ grid-template-columns:1fr; }} .wrap {{ padding:36px 18px 60px; }} }}
  footer {{ margin-top:56px; border-top:1px solid var(--line); padding-top:16px;
            font-size:13px; color:var(--muted); }}
  a {{ color:#0b5cad; }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>plant-ppi-screening</h1>
  <p class="lede">A harness for screening plant protein–protein interactions with
  structure prediction: resolve the proteins, batch the jobs within a free quota,
  parse the confidence metrics, and score the ranking against known positives and
  honest negatives.</p>
  <span class="pill">Harness complete · predictions not yet run</span>
  <nav>
    <a href="{REPO}">Repository</a>
    <a href="{REPO}/blob/main/docs/method.md">Method</a>
    <a href="{REPO}/blob/main/docs/curating-labels.md">Label protocol</a>
    <a href="{REPO}/blob/main/docs/running-predictions.md">Runbook</a>
  </nav>
</header>

<h2>The problem</h2>
<p>Finding an interaction by yeast two-hybrid or BiFC costs weeks per pair, so a
transcription factor family cannot be screened that way. Structure prediction
reverses the order of work: rank hundreds of pairs cheaply, then spend bench time on
the top few percent. On plant proteins the naive version fails quietly — few
structures are solved, alignments are thin, and disordered regions drag every
confidence score down. A pipeline that submits full-length sequences and sorts by
pLDDT looks confident and is wrong.</p>

<h2>What the harness does</h2>
<ol>
  <li><code>resolve</code> — gene symbols to UniProt entries, with a synonym fallback
      and explicit accession pinning for ambiguous symbols.</li>
  <li><code>check-labels</code> — rejects duplicate pairs, placeholder sources, and a
      negative class that is mostly easy decoys.</li>
  <li><code>batch</code> — jobs within the 30-per-day quota and the 5,000-token cap;
      over-budget pairs are skipped with a printed reason.</li>
  <li><code>ingest</code> / <code>evaluate</code> — ipTM and chain-pair PAE into a
      ranked table, AUC with bootstrap intervals, calibration gap reported separately.</li>
</ol>

<h2>Demo output <span class="tag">synthetic</span></h2>
<div class="fig">{figure}</div>
<p class="note">Synthetic scores, generated to prove the pipeline runs end to end.
No AlphaFold job has been submitted, so this page reports no biological result.</p>
<div class="metrics">{metric_html}</div>
{table_html}

<h2>Label set status</h2>
<p class="note">{benchmark} benchmark pairs, {calibration} calibration pairs,
{verified} of {len(labels)} rows verified. The evaluator refuses to compute metrics
while any included pair remains unverified.</p>
{label_html}

<h2>Next steps</h2>
<div class="grid">
  <div>
    <p><strong>Done.</strong> Resolution, validation, batching, parsing, ranking
    metrics, a dependency-free figure, and 36 offline tests running in CI on every push.</p>
  </div>
  <div>
    <p><strong>Not done.</strong> The predictions. Labels need literature
    verification, and the server accepts jobs only by hand at 30 a day.</p>
  </div>
</div>

<footer>
  Generated from <code>demo/report/report.md</code> by <code>site/build.py</code> ·
  MIT licensed · Disha Pirodiya ·
  <a href="{REPO}">{REPO.replace('https://', '')}</a>
</footer>
</div>
</body>
</html>
"""


def main() -> int:
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
