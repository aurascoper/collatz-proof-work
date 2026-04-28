# Changelog

## 2026-04-28 — Setup of autoresearch scaffolding

- Cloned `~/Downloads/CollatzConjecture(1).ipynb` to
  `~/Downloads/collatz-proof-work/CollatzConjecture_working.ipynb`
  (md5-verified identical to the original).
- The original notebook is **not** edited; all new code lives in
  `experiments/*.py` and supporting modules.
- Added directory layout:
    ```
    program.md
    score_proof_state.py
    experiments/
    proof_states/
    certificates/
    witnesses/
    verifiers/
    changelog.md
    README.md
    ```
- Initialised git history was already present; new artefacts are committed as
  separate runs.

## 2026-04-28 — Iteration 060c (K=8 c_val-split affine LP)

- New file: `experiments/iteration_060c.py`.
- Differences from 060a/060b:
  - Drift is attached to the **middle** window (`pi_1`):
    `d = popcount(pi_1) * (1 + log2 3) - K`,
    instead of `pi_2` as in 060a/060b.
  - Edges are grouped by `(E1, E2, c_val)` rather than `(E1, E2)` with
    `c_max` aggregation across mutually incompatible fibers.
  - The monotonicity constraint on `lambda` (`lam[E2] - lam[E1] <= 0`) is
    **removed**; this constraint forced `lam` to be constant inside any
    strongly connected component, which collapses the c_val split back to
    worst-case `c_max`. Without it, `lam[E2] >= 0` is a per-state slack
    that lets each fiber cope with its own depth shift.
- LP discipline:
  - Zero objective.
  - `psi[0]` anchored to 0.
  - `lam` bounded `[0, LAM_UB]` with `LAM_UB = 128` by default.
  - `scipy.optimize.linprog(method='highs')`; we report `res.status` and
    `res.message`.
- Numerical sentinel:
  - `v2(0)` saturates at 64 (window-scale), not 10^9. This avoids meaningless
    `c_val ~ 2e9` edges when an orbit lands exactly on an affine fixed
    point (e.g. the trivial 1->4->2->1 cycle).
- Witness extraction (when LP infeasible) runs Bellman-Ford in two
  abstractions:
  1. **Depth-free** (`lam = 0`): a negative cycle proves the LP is
     infeasible regardless of any choice of `lam`. This is a real
     drift-only obstruction.
  2. **Lambda-friendliest** (per-pair min `c_val`, `lam = LAM_UB`): a
     negative cycle here means even the most permissive `lam` weighting
     cannot satisfy the constraints, but the witness is `lam`-dependent
     and may be a stitching artefact.
- Smoke test at K=6 (262 143 fibers, 19 519 states, 204 429 edges):
  - LP infeasible.
  - Depth-free witness: a length-1 self-loop at `(r=63, pi=101010)` with
    drift +1.755. The affine fixed point of `pi=101010` is `n = -1`, so
    no positive integer realises this self-loop.
- **K=8 main run** (16 777 215 fibers, 535 168 states,
  12 725 664 (E1,E2,c_val)-edges; 16:09 -> 16:16):
  - LP **infeasible** (HiGHS status 2).
  - Counts: only 13 857 of the 12 725 664 c_val-split edges are *new*
    relative to the 12 711 807 unique (E1, E2) pairs. So the
    c_val-splitting differs from worst-case `c_max` by only 0.11 %.
    The hypothesis "over-aggregation of c_max" is *not* the dominant
    cause of infeasibility at K=8.
  - **Depth-free witness**: length-1 self-loop at
    `(r=255, pi=10101010)` with drift +2.340 and `c_val = -4`. The
    affine fixed point of `pi = 10101010` (m=4, S=4) is
    `B / denom = 65 / -65 = -1`; so no positive integer realises this
    self-loop. The K=8 LP is infeasible because of the same class of
    artefact as K=6 (self-loop at `(2^K - 1, alternating-bit pi)`,
    fixed point `n = -1`).
  - **Lambda-friendliest witness**: length-13 cycle with total drift
    -18.70 and total depth-effect +15; not realizable as a single
    integer orbit (denominator mismatch).
  - Conclusion: at the 2-window edge-state level the closed LP cannot
    be feasible regardless of `lambda`, but the obstruction is
    *structural / abstraction-induced*, not a real Collatz cycle. The
    next experiment is Iteration 061 (3-window
    trajectory-consistent states).
