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
- 2026-04-28 060d K=6: 3 / 11 realisable self-loops; dropping 8
  artefacts STILL infeasible.
- 2026-04-28 060d K=8: 0 / 26 realisable self-loops; dropping all 26
  artefacts STILL infeasible. Longer artefact cycles must exist.
- 2026-04-28 061 K=8 (sampled, 5 M random seeds): LP feasible,
  HiGHS Optimal. min_margin -2.5e-13 (boundary feasibility).
- 2026-04-28 061 K=8 (sampled, 10 M random seeds): LP **INFEASIBLE**
  (HiGHS status 2). The 5 M feasibility was a sampling artefact.
- 2026-04-28 061 K=8 v2 (with 3-window BF witness): infeasibility
  witness is a length-1 self-loop at
  `(r=254, pi=01010101, r=254, pi=01010101, r=254, pi=01010101)`,
  affine fixed point n=-2 (artefact). This is the **same artefact
  class** as 060c's K=8 witness `(255, 10101010)` -> fixed point n=-1,
  just phase-shifted. **The 3-window encoding does not remove it.**
- 2026-04-28 Iteration 062 ran the affine admissibility classifier on
  all 5 extracted witness cycles (K=6 060c x 2; K=8 060c x 2; K=8
  061 x 1). Result: **0 realisable, 5 non-realisable** (3 by negative
  denominator, 2 by non-integer fixed point). Every LP-infeasibility
  witness in the corpus is a provable abstraction artefact.
  Classifier is now wired into 060c and 061 for future runs.
- 2026-04-28 Iteration 063 (artefact-aware CEGIS, K=6, 300 rounds):
  every cut classified `non_realizable_negative_or_zero_denom`;
  ~3000 edges blocked of 204 429; LP still infeasible after 300
  rounds. Slow convergence: indicates a large structural
  artefact family rather than a finite list.
- 2026-04-28 Iteration 064 (positivity-domain theorem): proved that
  every positive-drift periodic ordinary-Collatz cycle has
  `denom = 2^S - 3^m < 0`, hence `n_pi <= 0`. Verified on **610
  witness cycles** across all iterations: `theorem_consistent = 610
  / 610 (100 %)`, `potentially_positive_int_fixed_point = 0`. Every
  LP-infeasibility witness in the corpus is a negative-domain
  artefact, not a Collatz cycle candidate. Recommends a
  positivity-aware LP reformulation as the next direction.
- 2026-04-28 Iteration 063 K=8 (50 rounds, 67 min): all 50 cycles
  classified `non_realizable_negative_or_zero_denom`; LP still
  infeasible. Same homogeneous artefact pattern as K=6.
- 2026-04-28 Iteration 065 (artefact family analysis): K=6 has 33
  distinct cycle lengths in artefacts (|denom| 19 to 10^52); K=8 has
  12 distinct cycle lengths (|denom| 65 to 2*10^35). Cleanly
  homogeneous family.
- 2026-04-28 Iteration 064 re-run (cumulative): 660 witness cycles
  examined across all runs; theorem still 100 % consistent;
  `potentially_positive_int_fixed_point = 0`.
- 2026-04-28 Iteration 066 (positivity-aware v_2-fuel lemma): proved
  that for any artefact cycle, eta(T_pi(n)) = eta(n) - S whenever
  T_pi(n) is integer. Verified arithmetically on 63 / 63 artefact
  cycles. Recommends a cycle-level Lyapunov term scaled by the
  cycle's total even-step count S_W as the LP-compatible fuel.
- 2026-04-28 Iteration 067 (eta-fuel Lyapunov thresholds): max
  required lambda over **653 positive-drift artefact cycles** is
  **lambda_max = log_2(3) - 1 = 0.584962500721157** exactly (same at
  K=6 and K=8). With Phi(n) = log_2 n + lambda * eta(n), every
  observed artefact cycle is contractive for any
  lambda > lambda_max. Structural explanation: the no-adjacent-odd-
  parity-bits constraint forces m <= T/2 = S for even T, capping
  drift/S at log_2 3 - 1. Cycle-level only (not yet a global LP
  certificate); next iteration (068) tests whether a compatible
  state potential psi exists.
- 2026-04-28 Iteration 068 (fixed-lambda psi-only LP): with
  `lambda_global = LOG2_3_UPPER - 1 + 1e-6`, the LP `psi[E2] -
  psi[E1] - lambda*S_edge <= -drift_edge - eps` is **FEASIBLE** at
  both K=6 (19 519 states, 203 615 edges) AND K=8 (535 168 states,
  12 711 807 edges) under HiGHS. min_margin essentially 0 (boundary
  feasibility), max_margin 22-31. First positivity-aware feasibility
  on the closed K=8 graph. NOT yet a Collatz proof: needs exact
  rational re-verification (069), realised-trajectory closure, and K
  scaling.
- 2026-04-28 Iteration 069a (exact rational verifier): re-checked
  every edge with `Fraction + LOG2_3_UPPER`. Both K=6 (0 / 203 615
  failures) and K=8 (0 / 12 711 807 failures) verify exactly with
  eps_q = 0. The 068 certificate is algebraically valid.
- 2026-04-28 Iteration 069b (semantic fuel audit): only **5.8 %
  (K=6)** and **2.3 % (K=8)** of edges have the LP credit -S_edge
  worst-case backed by an actual c_val. The 068 LP is a *cycle-
  reweighted* certificate, NOT a per-edge Lyapunov. A genuine
  per-edge fuel function eta(E, n) is the next missing ingredient.
- 2026-04-28 Iteration 070 (cycle-negativity interpretation): by LP
  duality + 069a, every directed cycle in the closed K=6 / K=8 graph
  has total weight w(C) = sum (drift(e) - lambda * S(e)) <= 0 exactly.
  Bellman-Ford on -w(e) at K=8 finds no positive-weight cycle within
  200 iterations. The binding self-loop has weight -rho*S = -4e-6
  exactly (matches the rho padding). Status: `exact_cycle_
  negativity_certificate_on_closed_K_graph` -- strictly weaker than
  Lyapunov descent but algebraically clean.

