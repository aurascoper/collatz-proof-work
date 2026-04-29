# Artifact policy

This repository follows a strict size-and-shape policy for generated
artefacts. The intent is that the public repo stays small, auditable,
and reproducible from source, while large machine-generated outputs
live outside git.

## What belongs in the repo

- **Source code.** Rust crate, Julia package, Python experiments and
  verifiers, runner scripts.
- **Compact JSON proof-states** under `proof_states/`. A proof-state is
  a per-iteration summary (counts, hashes, durations, status,
  classification breakdown) — never a full edge list, never a full
  word stream.
- **Certificates** under `certificates/` and **witnesses** under
  `witnesses/` whenever they fit comfortably in git (target: under
  ~5 MB per file; under ~50 MB total per iteration).
- **Prose artefacts**: `*.md` notes, audit and review documents, and
  the original Jupyter notebook.

## What does not belong in the repo

- **Full NDJSON streams** from the cycle exclusion engine
  (`cycle_exclusion_engine/out/*.ndjson`). These can reach multiple
  gigabytes; they are reproducible from source.
- **Full word enumerations** from the Rust generator
  (`cycle_exclusion_engine/out/words_*.bin` etc.).
- **Full LP edge tables** for $K \ge 8$. The closed-graph $K = 8$ LP
  has 12,711,807 edges; the certificate is a small JSON; the edge
  table itself is regenerated from code.
- **Per-iteration logs** beyond a small banner. Detailed logs live in
  `cycle_exclusion_engine/logs/` locally and are gitignored.

## Compact summaries

When an iteration produces a large raw artefact, commit a *summary*
JSON next to it that records:

- iteration tag and pipeline mode,
- input parameters (e.g. `T_MAX`, `K`, sample size),
- output counts and classification breakdown,
- end-to-end duration,
- status one-of: `EXACT`, `CLOSED-SYM`, `SAMPLED`, `DIAGNOSTIC`,
  `INVALIDATED`, `deferred`,
- a short `note` explaining what was omitted and why.

Example: `proof_states/iteration_073_periodic_cycle_engine_T36_summary.json`
is the committed summary; the full T36 NDJSON is gitignored.

## Reproducing a deleted or oversized artefact

Every committed summary should be re-derivable by running the
corresponding script from `experiments/`, `verifiers/`, or
`cycle_exclusion_engine/scripts/`. If a summary is in the repo but
the script that produced it is not, that is a bug — open an issue.

## Status categories

The five status categories used across the repo are:

- **EXACT** — verified in exact $\mathbb{Q}$ arithmetic or in BigInt
  arithmetic, with zero failures over the stated domain.
- **CLOSED-SYM** — closed symbolic / structural result that does not
  reduce to per-trajectory dynamics on positive integers.
- **SAMPLED** — established only on a sample; the result may not
  survive the full domain. Not citable as exact.
- **DIAGNOSTIC** — useful for ranking or debugging; not an exclusion
  mechanism on its own.
- **INVALIDATED** — superseded or refuted by a later iteration; kept
  for the historical record.

These categories are normative across all README, audit, review, and
changelog entries. Reusers are asked to preserve them in derivative
works.
