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

The repository root is configured to deploy, so either folder works:

```bash
npx vercel login          # once, if the CLI reports an invalid token
npx vercel --prod         # from the repository root
```

Two files make the root work, and both matter:

- `vercel.json` pins `"framework": null` and rewrites `/` to `site/index.html`,
  so the Python harness is no longer mistaken for a Python web app. There is no
  build step: the page is already built when it is committed.
- `.vercelignore` keeps the Python sources, tests, data and demo out of the
  upload, which is both faster and a guarantee that none of it can be served.

Deploying from inside `site/` also works and needs no configuration, because that
folder contains only `index.html`.

### The two errors people hit

| Error | Cause | Fix |
| --- | --- | --- |
| `[PYTHON_ENTRYPOINT_NOT_FOUND]` | Deployed a folder with `*.py` and `requirements.txt` but no `app.py`/`api/index.py`, so Vercel tried to run it as a Python web app | Root now has `vercel.json`; or deploy from `site/` |
| `The specified token is not valid` | Expired CLI session, not a project problem | `npx vercel login` |

After a deploy, open the production URL and confirm the page renders: a 200 alone
is not proof, since a rewrite can succeed while the asset is missing.
