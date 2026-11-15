# Curating 25 honest labels

Twenty-five verified pairs beat sixty guesses. This is the procedure, in order,
with the decision rules that keep the set defensible. Budget two evenings.

The rule underneath all of it: **a label is only a label if you could show a
reviewer where it came from.** "Everyone knows these interact" is not a source.

## Step 1 — fix the protein set before looking at anything

Choose 8–10 proteins and do not add more later. For the group I bZIP project:

| Gene | UniProt | Note |
| --- | --- | --- |
| VIP1 | Q9MA75 | transcription factor; two Arabidopsis genes share this symbol |
| BZIP29 | Q8H1F0 | group I bZIP |
| BZIP30 | Q9SIG8 | group I bZIP |
| AGB1 | P49177 | stored in UniProt as `GB1`, locus At4g34460 |
| RCN1 | resolve it | PP2A A subunit, a known partner of the B″ family |
| plus 2–4 further group I bZIPs | `python cli.py resolve` | PosF21 and close homologues |

Ten proteins give 45 unordered pairs, which is more than you need. Eight gives 28.
Pick the set you can actually read about.

## Step 2 — build the pair grid

Every unordered pair once. A short script, run once:

```bash
python - <<'EOF'
genes = ["VIP1", "BZIP29", "BZIP30", "AGB1", "RCN1"]
rows = []
for i, a in enumerate(genes):
    for b in genes[i + 1:]:
        rows.append(f"{a}_{b},{a},{b},,,,,1,positive_curated,,no")
print("pair_id,gene_a,gene_b,acc_a,acc_b,range_a,range_b,label,label_type,source,verified")
print("\n".join(rows))
EOF
```

Paste the output into `data/candidates.csv` under the existing header. Labels stay
empty-on-purpose: they default to `1` so the validator warns you about every row
you have not touched yet.

## Step 3 — search in this order, stop at the first real source

1. **The lab's own papers.** VIP1 and the PP2A B″ subunits are Tsugama's own work;
   start there, because a lab's own interactions are the ones a supervisor will ask about.
2. **PubMed**, with method words, not just gene names:
   ```
   (VIP1 OR "bZIP29" OR "bZIP30") AND (interact* OR "two-hybrid" OR BiFC OR "pull-down")
   ```
   ```
   AGB1 AND (VIP1 OR bZIP) AND Arabidopsis
   ```
3. **Interaction databases as leads only:** BioGRID, IntAct. They list the
   experiment type and the PMID, so use them to find the paper, then read the paper.
4. **STRING is not evidence.** A high score is a prediction from co-expression,
   text mining and orthology. It can suggest a pair to look up; it cannot label one.

For each pair, open the abstract and the figure legend. If the interaction is only
in the abstract of a review, follow the reference the review cites.

## Step 4 — apply the decision rules

| What you found | Label | `label_type` |
| --- | --- | --- |
| A direct experiment (Y2H, BiFC, Co-IP, pull-down, split-luciferase) in Arabidopsis or a stated ortholog | 1 | `positive_curated` |
| Tested directly and no interaction detected | 0 | `negative_curated` |
| No experiment either way | — | leave `verified=no`, exclude from scoring |
| A pair constructed to be implausible (membrane kinase vs nuclear TF) | 0 | `decoy_localization` |
| A predicted or database-inferred interaction only | — | not a label |

Two traps that quietly ruin benchmarks:

- **"No interaction found" is not proof of no interaction.** Negative results are
  rare and often only reported as "data not shown". Prefer decoys over claiming
  negatives you cannot cite.
- **Orthologs are weaker evidence.** A rice homologue interacting does not
  automatically mean the Arabidopsis pair does. If you use one, say so in the source.

## Step 5 — write the source so a stranger can check it

Format: author, year, journal, method, identifier.

```
Tsugama et al. (2012) Plant Physiol, Y2H + BiFC; PMID 22467755
```

Not `"paper on VIP1"`. The point of the column is that someone else can verify your
row in under a minute, and that you can defend it in an interview.

## Step 6 — verify before you flip the flag

Four checks per row:

1. **Species** — Arabidopsis, or an explicitly stated ortholog.
2. **Identifiers** — the gene in the paper is the accession in your row. This is
   where VIP1 (two genes, Q9MA75 and F4J8C6) burns people.
3. **Method** — a direct assay, not co-expression or a prediction.
4. **Direction** — no duplicate pair in reverse order; the validator rejects it.

Then set `verified=yes`.

## Step 7 — validate the file, then freeze it

Every ten rows:

```bash
python cli.py check-labels
```

What good output looks like at 25 pairs:

```
candidates.csv: 27 pairs | 12 positive | 15 negative (9 decoys, 6 curated) | 27 verified | 2 calibration
label file looks consistent
```

Warnings are usually right. "50% of pairs are decoys" means your metrics will look
better than the biology. Aim for decoys below 40% of the set.

**Then commit the file before you see any prediction.**

```bash
git add data/candidates.csv && git commit -m "Freeze label set (25 pairs) before screening"
```

Editing labels after seeing scores is how a benchmark becomes a story you told
yourself. The commit date is your evidence that you did not.

## Step 8 — run, then report honestly

```bash
python cli.py batch
# submit at alphafoldserver.com, download, unpack into results/
python cli.py ingest --results results/
python cli.py evaluate --results results/scores.csv
```

Report the AUC **with its interval**, the recall in the top decile, and the decoy
scores separately. If the number is bad, report the bad number — for plant proteins
a weak result is a legitimate finding, and it is the exact question the project asks.

## What a realistic 25-pair set looks like

| Class | Count | Why that number |
| --- | --- | --- |
| `positive_curated` | 10–12 | enough for a stable AUC ranking |
| `negative_curated` | 4–6 | only pairs actually tested and found not to interact |
| `decoy_localization` | 8–9 | keep under 40% of the total |
| `calibration` | 1–2 | BRI1–BAK1 full-length versus domains; never in the metrics |

If you cannot find six curated negatives, use more decoys and say so in the report.
Inflating the negative class with pairs nobody tested is the one shortcut that
invalidates everything downstream.
