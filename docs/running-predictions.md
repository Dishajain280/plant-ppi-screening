# Running the predictions

The AlphaFold Server has no public API, so the pipeline stops at a JSON file that
a human submits. This is a terms-of-use constraint, not a missing feature. Budget
about twenty minutes of clicking for the first batch, then a few minutes a day.

**Cost: free. Limit: 30 jobs per day, 5,000 tokens per job.** The quota refreshes
at midnight UK time.

## 0. Before you submit anything

```bash
python cli.py resolve          # gene symbols -> UniProt accessions + sequences
python cli.py batch            # -> batches/batch_001.json (+ a token count per job)
```

`batch` prints how many jobs it planned and skips any pair that exceeds 5,000
tokens, with the reason. Read the skip list before continuing: a silently dropped
pair looks like a negative in the results.

Check the candidate list one more time. Anything with `verified=no` will block
scoring later, by design. That is fine for the calibration run and fatal for a
real result.

## 1. Sign in

Go to **https://alphafoldserver.com** and sign in with a Google account.

The terms matter here: use is limited to **non-commercial** work by non-commercial
organisations, and output must not be used to train a similar structure-prediction
model. An undergraduate research project at a university is squarely inside those
terms. A project for an employer would not be.

## 2. Upload the batch file

On the AlphaFold Server home page, click **Upload JSON** and choose
`batches/batch_001.json`.

Each file may contain up to 100 jobs. Imported jobs land in **History** as **saved
drafts** — nothing has run yet, and no quota has been spent.

Your account can hold up to 500 saved drafts, so a full screen of candidates is
not a problem.

## 3. Run the drafts

Open a draft, check the two chains and the job name, then submit it. Each
submission consumes one job from the daily allowance.

Because the limit is 30 a day, the practical pattern is:

| Day | Action |
| --- | --- |
| 1 | Upload the file, submit up to 30 drafts |
| 2 | Submit the next 30, download yesterday's completed jobs |
| 3 | Submit the remainder, collect everything |

If you try to submit more than the quota allows, the extra jobs stay as drafts —
nothing is lost, they simply wait for the reset.

Do **not** script the web interface to bypass the quota. The terms are explicit
about automation, and an account that abuses them loses access mid-project.

## 4. Download the results

Each finished job has a download button; download the zip. Unpack every zip into
one folder:

```
results/
├── fold_BRI1_BAK1_full/
│   ├── fold_BRI1_BAK1_full_model.cif
│   ├── fold_BRI1_BAK1_full_summary_confidences.json
│   ├── fold_BRI1_BAK1_full_full_data_0.json
│   └── ...
└── fold_VIP1_BZIP29/
    └── ...
```

Keep the folder names. The job name is how a result is matched back to a candidate,
and the parser strips the `fold_` prefix automatically.

## 5. Ingest and score

```bash
python cli.py ingest --results results/
python cli.py evaluate --results results/scores.csv
```

`ingest` writes one row per job to `results/scores.csv` with ipTM, pTM, the minimum
chain-pair PAE and the clash flag. `evaluate` joins those against the labels and
writes `report/report.md` and `report/figure.svg`.

If `evaluate` exits with status 2, it is telling you which labels are still
unverified. That is the guard working, not a bug.

## 6. Read the result like a scientist

- An **AUC of 0.5** means the ranking is no better than chance. That is a real,
  reportable finding — these models are known to struggle on plant proteins, and
  it is the exact question the project asks.
- **Recall in the top decile** is the number that matters operationally. A screen
  is useful if real interactions reach the top of a list a human will read.
- Check the **calibration pair first**. If BRI1–BAK1 full-length scores far below
  its truncated domains, the pipeline is behaving as published work predicts
  (roughly 0.38 versus 0.90 ipTM). If it does not, stop and investigate before
  trusting any other number.

## If the server is unavailable

Alternatives that take the same protein pairs:

- **Boltz-2** (MIT licence, runs on a 24 GB GPU, free Colab notebook available)
- **ColabFold / AlphaFold2-multimer** (free Colab T4, complexes up to roughly
  2,000 residues)
- **Chai-1** (Apache 2.0)

These produce different metrics from AlphaFold 3, so do not mix sources inside one
benchmark. Convert the batch file to the tool's own input format and record which
predictor produced each row; the report must name it.

## Record keeping

Keep `batches/`, `results/scores.csv` and the `report/` folder together, plus the
date of each submission. `.gitignore` intentionally excludes `batches/` and
`results/` because they are large and licence-bound, so archive them locally — a
reviewer asking "how many pairs did you actually run?" deserves a checkable answer.
