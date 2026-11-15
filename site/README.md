# Project site

A single static page describing this repository: the problem, what the harness
does, the demo figure, the metrics, and the label-set status.

## Design

One file, no JavaScript, no web fonts, no external requests — so it renders the
same offline and deploys as a plain static asset.

- A small design system of CSS custom properties (colour, radius, shadow) with a
  light and a dark theme chosen by `prefers-color-scheme`.
- Four KPI cards at the top, built from the same numbers the report prints.
- The figure is inlined as SVG, not shipped as an image, so it stays crisp and the
  page loads in one request.
- Tables mark known interactors with a green edge and numbers use tabular figures,
  so the ranking is readable at a glance.
- The status section states what is **not** done as prominently as what is; the
  demo figure keeps its `SYNTHETIC` label until real jobs have run.

## Why this exists instead of a Python deployment

Deploying the repository root to Vercel fails with `PYTHON_ENTRYPOINT_NOT_FOUND`.
That is not a bug: `requirements.txt` plus the `*.py` files make Vercel classify
the project as a Python web application, which requires a server entrypoint such as
`app.py` or `api/index.py`.

But there is no web application here. The harness is a command-line tool that
batches jobs for the AlphaFold Server, which has no public API and no GPU. Nothing
could be served that a static page does not already say better.

So the deployable artifact is this folder: pure HTML, no build step at deploy time,
no Python runtime.

## Build

```bash
python site/build.py      # regenerates index.html from demo/report/ and data/
```

`build.py` reads `demo/report/report.md`, `demo/report/figure.svg` and
`data/candidates.csv`, so the page cannot drift from the repository. Commit the
regenerated `index.html` along with whatever changed in the report.

`index.html` is ~22 KB and self-contained, so it can also be opened directly from
disk with no server.

## Deploy

```bash
cd site
npx vercel login          # once
npx vercel --prod         # deploy
```

Deploy from inside `site/`, not from the repository root — the root still contains
the Python files that trigger the detection error. Vercel serves `index.html`
directly; no framework preset, build command or `vercel.json` is needed.
