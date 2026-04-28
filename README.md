# Collatz Proof-Engineering Work

This directory is a reproducible computational pipeline for studying the
ordinary Collatz map. It is **not** a proof of the Collatz conjecture and
no script in here is permitted to claim one (see `program.md`).

## What is in here

| Path                                       | What it is                                             |
|--------------------------------------------|--------------------------------------------------------|
| `CollatzConjecture_working.ipynb`          | Working copy of the original notebook (md5-identical). |
| `program.md`                               | Agent rules / proof protocol.                          |
| `experiments/iteration_060c.py`            | K=8 closed affine residue-aware LP, c_val-split.       |
| `proof_states/iteration_*.json`            | One JSON proof_state per experiment.                   |
| `certificates/iteration_*_certificate.json`| LP solutions when the LP is feasible.                  |
| `witnesses/iteration_*_cycle.json`         | Cycle witnesses when the LP is infeasible.             |
| `verifiers/verify_certificate.py`          | Exact rational re-verifier (Fraction + log2_3 upper).  |
| `score_proof_state.py`                     | Structured scorer for proof_state JSON files.          |
| `changelog.md`                             | Human log of changes per run.                          |

## What is proven, sampled, or open

### Closed symbolic results
- F_38 = 39 088 169: the count of length-36 admissible parity words for
  ordinary Collatz (no two adjacent 1-bits) was confirmed by exhaustive DFS
  in iteration 057.
- The affine-cylinder boundary residue formula was verified at K=6: for
  every parity mask of length 6 the affine recurrence
  `B := 3B + 2^S` (odd) / `S += 1` (even) reproduces direct simulation
  exactly.

### Sampled / empirical results
- Up to ~12M sampled trajectories at K=24 fed iterations 49-52 of the
  notebook. These results constrain the LP but are **not** universal.
- Per-`(E1, E2, c_val)` edge counts in 060c are based on exhaustive
  enumeration of `n0 mod 2^{3K}` only. They are universal at the residue-
  abstraction level but say nothing about Collatz on `n > 2^{3K}`.

### Negative / abstraction-artefact results
- The 2-window edge-state abstraction admits closed cycles that no actual
  positive-integer trajectory ever realises. Examples found by 060c:
    - K=6: a self-loop at `(r=63, pi=101010)` whose affine fixed point
      is `n = -1`.
    - K=8: see `proof_states/iteration_060c.json` for the witness.
- These cycles cause the closed LP to be infeasible without implying any
  Collatz cycle exists.

### Open
- Whether **3-window** (or higher-order) state encodings eliminate all
  abstraction-artefact cycles. Iteration 061 is the first sketch of this.
- Whether an exact rational certificate can be produced at K >= 8 using
  `LOG2_3_UPPER` instead of float `log2(3)`.
- Whether scaling K (10, 12, 16) preserves feasibility once the
  abstraction is tight enough.

## Running an experiment

```bash
cd ~/Downloads/collatz-proof-work
ITER_K=8 python3 experiments/iteration_060c.py
```

Environment variables:
- `ITER_K`: window length (default 8).
- `ITER_EPS`: LP slack (default 0.01).
- `ITER_LAM_UB`: upper bound for `lambda` (default 128.0).
- `ITER_EXHAUSTIVE`: 1 = exhaustive over `n0 mod 2^{3K}`, 0 = random sampling.
- `ITER_RANDOM_SAMPLES`: number of random samples when `ITER_EXHAUSTIVE=0`.

## Run notes

- 2026-04-28 060c K=6 smoke: 19 519 states, 204 429 edges. LP infeasible.
  Depth-free witness = self-loop at (r=63, pi=101010), affine fixed point
  n=-1 (artefact). Total runtime 60 s.
- 2026-04-28 060c K=8 main: 535 168 states, 12 725 664 c_val-split edges.
  LP infeasible. Depth-free witness = self-loop at (r=255, pi=10101010),
  affine fixed point n=-1 (artefact). c_val splitting fanout vs (E1,E2)
  pairs: only 0.11 %. Total runtime 439 s.
- Conclusion: the 2-window edge-state abstraction is structurally too
  coarse at every K we have tried. Next: Iteration 061 (3-window) and a
  cleanup that filters self-loops whose affine fixed points are not in
  Z_{>0}.

