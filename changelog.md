# Changelog

## 2026-04-28 — Setup of autoresearch scaffolding

- Cloned `~/Downloads/CollatzConjecture(1).ipynb` to
  `~/Downloads/collatz-proof-work/CollatzConjecture_working.ipynb`
  (md5-verified identical to the original).
- The original notebook is **not** edited; all new code lives in
  `experiments/*.py` and supporting modules.
- Added directory layout: `program.md`, `score_proof_state.py`,
  `experiments/`, `proof_states/`, `certificates/`, `witnesses/`,
  `verifiers/`, `changelog.md`, `README.md`.

## 2026-04-28 — Iteration 060c (K=8 c_val-split affine LP)

- New file: `experiments/iteration_060c.py`.
- Differences from 060a/060b:
  - Drift attached to the **middle** window (`pi_1`):
    `d = popcount(pi_1) * (1 + log2 3) - K`, instead of `pi_2`.
  - Edges grouped by `(E1, E2, c_val)` rather than `(E1, E2)` with
    `c_max` aggregation.
  - The monotonicity constraint on `lambda` is **removed**; this
    constraint forced `lam` to be constant inside any SCC, collapsing
    the c_val split back to worst-case `c_max`.
- LP discipline: zero objective, `psi[0]` anchored to 0, `lam` bounded
  `[0, 128]`, `scipy.optimize.linprog(method='highs')`,
  `res.status`/`res.message` reported.
- Numerical sentinel: `v2(0)` saturates at 64 (window-scale), not 10^9,
  to avoid meaningless `c_val ~ 2e9` edges when an orbit lands exactly
  on an affine fixed point (e.g. the trivial 1->4->2->1 cycle).
- Witness extraction runs Bellman-Ford (capped at 200 iters) in two
  abstractions:
  1. Depth-free (`lam = 0`): a negative cycle is `lam`-independent and
     proves a real LP obstruction.
  2. Lambda-friendliest (per-pair min `c_val`, `lam = 128`):
     `lam`-dependent witness, may be a stitching artefact.
- **K=6 smoke test**: 19 519 states, 204 429 edges; LP infeasible;
  depth-free witness = self-loop at `(r=63, pi=101010)`; affine fixed
  point n=-1 so non-realisable.
- **K=8 main run**: 16 777 215 fibers, 535 168 states,
  12 725 664 (E1,E2,c_val)-edges; LP infeasible (HiGHS status 2).
  Only 13 857 of the c_val-split edges are *new* relative to
  12 711 807 unique (E1,E2) pairs (0.11 % fanout). Therefore the
  "over-aggregation of c_max" hypothesis is *not* the dominant cause
  of K=8 infeasibility.
- Depth-free K=8 witness: length-1 self-loop at `(r=255, pi=10101010)`
  with drift +2.340 and `c_val = -4`; affine fixed point n = -1 so
  non-realisable.
- Lambda-friendliest K=8 witness: length-13 cycle, total drift -18.70,
  total depth-effect +15; not integer-realisable as a single orbit.
- Conclusion: at the 2-window edge-state level the closed LP cannot
  be feasible regardless of `lambda`, but the obstruction is
  *structural / abstraction-induced*, not a real Collatz cycle.

## 2026-04-28 — Iteration 060d (artefact self-loop filter)

- New file: `experiments/iteration_060d_filter_artifact_selfloops.py`.
- For every (r, pi) precompute the affine fixed point
  `f_pi = B / denom` and check whether it is a positive integer with
  `f_pi mod 2^K == r`. Self-loops `(r, pi, r, pi) -> (r, pi, r, pi)`
  whose f_pi fails this test are abstraction artefacts that no integer
  trajectory ever realises.
- K=6: 3 of 11 self-loops are realisable; dropping the 8 artefact
  self-loops leaves the LP **still infeasible**.
- K=8: 0 of 26 self-loops are realisable; dropping all 26 leaves the
  LP **still infeasible**.
- Therefore: the 2-window encoding contains *longer* abstraction
  artefact cycles, not just self-loops. Filtering self-loops alone is
  not enough.

## 2026-04-28 — Iteration 061 (3-window state encoding)

- New file: `experiments/iteration_061_3window.py`.
- States: S = (r1, pi0, r2, pi1, r3, pi2). Transitions shift by one
  window and use pi_middle = pi_2 (the executed window).
- 5 000 000 random samples (sampled, **not** exhaustive over
  n0 mod 2^32 = 4.29 B fibers).
- **K=8 sampled result**: 6 999 495 states, 4 965 744 edges, LP
  **feasible** (HiGHS status 7, Optimal). min_margin -2.5e-13 (boundary
  feasibility), max_margin 3052.97. Total runtime 148 s.
- Caveat: this does NOT prove Collatz. It is only a *necessary*
  condition for a closed 3-window certificate. To upgrade:
  (a) exhaustively enumerate n0 mod 2^{4K} = 2^32 fibers
      (Numba/C++ required; ~256x more than 060c), or
  (b) prove closure deductively via affine residue structure.
- The 3-window encoding clearly removes the dominant K=6/K=8 artefact
  class (self-loops at (2^K - 1, alternating-bit pi)) by preventing
  them from forming closed cycles in the wider state space.
