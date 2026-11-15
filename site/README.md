# Project site

A single static page describing this repository: the problem, what the harness
does, the demo figure, the metrics, and the label-set status.

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

## Deploy

```bash
cd site
npx vercel login          # once
npx vercel --prod         # deploy
```

Deploy from inside `site/`, not from the repository root — the root still contains
the Python files that trigger the detection error. Vercel serves `index.html`
directly; no framework preset, build command or `vercel.json` is needed.
