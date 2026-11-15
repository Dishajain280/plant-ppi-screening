# Method

This note states exactly what the harness does, what each number means, and
where the reasoning is weak. It is deliberately short enough to check; the
intended use is as the skeleton of a longer technical report.

## Protocol

1. **Define the question.** One protein family, one organism, one type of
   interaction. Broadening the scope after seeing the scores is how a benchmark
   becomes a fishing trip.
2. **Build the candidate list.** Every row needs a label, a label class, and a
   source. Rows without a source are still allowed, but they cannot be scored.
3. **Resolve sequences.** Gene symbols are mapped through UniProt; ambiguous
   symbols and non-standard gene names must be pinned by accession.
4. **Calibrate on a known pair.** Run a literature-established interaction both
   full-length and truncated to its interacting domains. If the harness does not
   reproduce the expected gap between the two, nothing downstream is trustworthy.
5. **Truncate before scaling.** Plant proteins frequently exceed the 5,000-token
   job limit. Domain boundaries come from InterPro or from the ordered core of a
   full-length prediction (drop flanks below pLDDT 70 and re-run).
6. **Screen within quota.** 30 jobs per day, recorded so the count is auditable.
7. **Score, then look at the ranking.** Metrics are computed only after every
   included label has been checked against its source.

## Definitions

Let `n+` be the number of labelled positives, `n-` the number of negatives, and
`s(i)` the ipTM of pair `i`.

| Metric | Definition | Why it is reported |
| --- | --- | --- |
| AUC | Probability a random positive outranks a random negative (ties count 0.5) | Threshold-free summary of ranking quality |
| 95% CI | Percentile bootstrap, 2,000 resamples | With 40 pairs, a bare AUC overstates certainty |
| Recall@top-k | Positives in the top `ceil(0.1 n)` divided by `n+` | Answers the operational question: how many real interactions survive triage |
| Precision@τ | Positives among pairs scoring ≥ τ | Answers the cost question: how much bench time per hit |

The primary metric is **recall in the top decile**, not AUC. A screen is useful
when it puts real interactions near the top of a list a human will read, and AUC
can look respectable while the top of the list is polluted.

## Reading confidence scores

- **ipTM** — accuracy of the relative placement of the two chains. Above ~0.8
  indicates a confident interface; below ~0.6 usually means the model failed to
  find one; 0.6–0.8 is a grey zone that must not be reported as a hit.
- **chain-pair PAE minimum** — the smallest predicted alignment error between the
  two chains. This is the metric that survives disordered regions, which drag
  global pTM and ipTM down even when the folded domain is correct.
- **pLDDT** — per-residue local confidence. Necessary, never sufficient: a
  well-folded monomer says nothing about whether it binds its partner.
- **ranking_score** — an internal composite (0.8·ipTM + 0.2·pTM, penalised for
  clashes and disorder). Useful for ordering within one job, not for comparing
  across jobs.

## Label classes

| Class | Meaning | Risk |
| --- | --- | --- |
| `positive_curated` | Interaction reported in a cited experiment | Literature bias toward easy, well-studied pairs |
| `negative_curated` | Tested and not detected | Absence of detection is not absence of interaction |
| `decoy_localization` | Pair constructed to be implausible, e.g. plasma-membrane kinase versus nuclear transcription factor | Easy negatives inflate every metric |

Random pairs are **not** used as negatives. Two proteins that never meet in a cell
are trivially separable, and a model that learns "membrane versus nucleus" will
score well while learning nothing about interfaces. Decoys are reported separately
from curated negatives so the inflation is visible.

## Integrity rules enforced in code

- `evaluate` exits with status 2 while any included label has `verified=no`.
- Over-budget jobs are skipped with a printed reason; they are never silently
  dropped, because a silently dropped pair looks like a negative.
- The daily quota is written to a local file, so a run can be audited afterwards.
- The demo report is labelled synthetic in the report body, not only in the README.

## Known limitations

1. **Single-model evidence.** One predictor, one seed. Agreement across Boltz-2,
   Chai-1 and AlphaFold 3 would be far stronger evidence than any ipTM threshold.
2. **No experimental validation.** A high score is a hypothesis. The loop this
   project is built for is prediction → Y2H or BiFC → updated labels.
3. **Truncation changes the question.** A domain pair that scores well says nothing
   about whether the full-length proteins interact in a cell, where disordered
   regions, crowding and post-translational modification matter.
4. **Small n.** Dozens of pairs give wide confidence intervals. Reporting them is
   the point; hiding them would be the error.
5. **Label leakage.** If a pair appears in the training data of the predictor, its
   score is not an independent test. Curated interactomes overlap with what these
   models have seen, and no clean fix exists at this scale.

## Planned validation

- Reproduce the published full-length versus domain-level gap on BRI1–BAK1.
- Screen one bZIP family with ≥30 curated pairs and report AUC with its interval.
- Test whether gains hold on a held-out family never used for calibration.
