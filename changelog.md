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
- **K=8 sampled result, 5 M seeds**: 6 999 495 states, 4 965 744 edges,
  LP feasible (HiGHS Optimal), min_margin **-2.5e-13** (numerical
  boundary), max_margin 3052.97. Total runtime 148 s.
- **K=8 sampled result, 10 M seeds (autonomous follow-on)**: 10 968 844
  states, 9 865 835 edges, LP **INFEASIBLE** (HiGHS status 2). Total
  runtime 240 s.
- The 5 M feasibility was a *sampling artefact*: it sat on the LP
  boundary (-2.5e-13 margin), and with twice the samples the
  constraint set tightens enough to break feasibility. The 3-window
  encoding does NOT, on the evidence so far, give a feasible closed
  LP at K=8 either.
- Caveat: 10 M is still ~0.23 % of the closed graph (n0 mod 2^{4K} =
  2^32 = 4.29 B fibers). Both results are sampled. The infeasibility
  *might* be another sampling artefact in the opposite direction --
  i.e., 10 M samples include a few coincidental cycles whose intersect
  is empty. We currently have no witness extraction for the 3-window
  LP; that is the next gap.
- To upgrade either way:
  (a) exhaustively enumerate n0 mod 2^{4K} = 2^32 fibers (Numba/C++
      required; ~256x more than 060c), or
  (b) prove closure deductively via affine residue structure.
- Take-home: the 3-window encoding does eliminate the dominant K=6/K=8
  *self-loop* artefact (`(2^K - 1, alternating-bit pi)`), but other
  longer cycles remain in play and at least some are visible at 10 M
  samples.

## 2026-04-28 — Iteration 061 v2 (with 3-window witness extractor)

- Added Bellman-Ford witness extraction (depth-free abstraction) to
  `experiments/iteration_061_3window.py`.
- Re-ran 10 M K=8 with the new witness extractor.
- **Witness**: a length-1 self-loop at the 3-window state
  `S = (r=254, pi=01010101, r=254, pi=01010101, r=254, pi=01010101)`,
  drift +2.340, c_val -4. Affine fixed point of `pi=01010101` is
  `f = B / denom = 130 / -65 = -2`. **Not** a positive integer; no
  positive Collatz orbit realises it.
- This is the *same artefact class* as the 2-window K=8 060c witness
  `(r=255, pi=10101010)` -> fixed point n=-1; just phase-shifted.
  The 3-window state encoding does NOT remove this artefact, because
  the self-loop has all three sub-states identical and reduces to a
  2-window self-loop test, which still has zero realisable instances
  at K=8 (per 060d).
- Therefore: the user's recommendation "implement 3-window
  trajectory-consistent states" alone is insufficient. Either:
  (a) filter the 3-window self-loops the same way 060d filters
      2-window self-loops, or
  (b) abandon the (r, pi) abstraction and use a value-aware encoding
      that distinguishes the affine fixed point from real positive
      integers.

## 2026-04-28 — Iteration 062 (affine cycle admissibility classifier)

- New module: `verifiers/cycle_classifier.py` exposing
  `classify_cycle(pi_middles, K)`. Pipeline:
    1. Concatenate `pi_middle` bits in time order (MSB = first step).
    2. Compose A, B, S exactly via the canonical recurrence.
    3. Solve `(2^S - 3^m) n = B`.
    4. Realisable iff `denom > 0`, `B % denom == 0`, `n > 0`, AND
       arbitrary-precision direct simulation from n traces the cycle
       and returns to n.
- New script: `experiments/iteration_062_classify_witnesses.py`
  walks `witnesses/iteration_*_cycle*.json`, classifies every cycle
  and writes `<basename>_classified.json` plus a summary
  `proof_states/iteration_062_classifier.json`.
- Result on the 5 previously-extracted witnesses:
    - `non_realizable_negative_or_zero_denom`: 3
    - `non_realizable_non_integer_fixed_point`: 2
    - `REALIZABLE_POSITIVE_INTEGER_CYCLE`: 0
- Every LP-infeasibility witness we have produced is **provably an
  abstraction artefact**. There are zero putative real Collatz cycles
  in our witness corpus.
- Integration: `experiments/iteration_060c.py` and
  `experiments/iteration_061_3window.py` both now import and call
  `classify_cycle` during witness extraction. The classification is
  attached to each cycle payload; **no LP constraints are removed**.

## 2026-04-28 — Iteration 063 (artefact-aware CEGIS)

- New script: `experiments/iteration_063_artifact_cegis.py`.
- Loop:
    1. Build closed K=8 LP (c_val-split).
    2. Solve. If feasible -> stop.
    3. If infeasible -> depth-free Bellman-Ford witness.
    4. Classify with 062 classifier.
    5. If REALIZABLE_POSITIVE_INTEGER_CYCLE -> stop and emit candidate.
    6. Else -> diagnostic cut: block all (E1, E2, c_val) edges sharing
       any (E1, E2) pair from the witness cycle (every depth-free BF
       cycle has positive total drift hence denom < 0 hence non-
       realisable; cuts are guaranteed safe by the classifier).
    7. Re-solve.
- Structural observation: the LP is feasible iff the depth-free graph
  has no positive-drift cycle. So the CEGIS loop terminates exactly
  when *all* positive-drift cycles have been broken. The classifier
  serves as a sanity check; by construction it never returns
  REALIZABLE for a depth-free BF witness because positive total drift
  forces 2^S < 3^m hence denom < 0.
- K=6 / 300 rounds: 300 non-realisable cycles cut (~3 000 edges blocked
  out of 204 429); LP remains infeasible. Cycle lengths range 1-34.
  Combinatorics are heavy; convergence will need many more rounds (or
  a structural argument). Runtime 220 s.
- Take-home: the classifier successfully gates every cut as
  artefact-only; the question of whether finitely many cuts suffice
  to make the LP feasible is open and likely a graph-combinatorial
  bound rather than a Collatz statement.

## 2026-04-28 — Iteration 063 K=8 (50 rounds, ~67 min)

- 50 rounds of artefact-aware CEGIS at K=8.
- Every round's witness classified `non_realizable_negative_or_zero_denom`.
- 425 (E1, E2, c_val) edges blocked of 12 725 664 total.
- Cycle-length histogram heavily concentrated: length 5 dominates
  (25/50 = 50 %), then length 10 (10/50), with rare lengths 1, 3, 4,
  6, 7, 9, 12, 18-20.
- LP remains infeasible after 50 rounds.
- Per the K=8 metrics requested:
  - `any_realizable_positive_integer_cycle`: false
  - `any_non_integer_fixed_point_with_denom>0`: false (all denoms negative)
  - `any_zero_denom_cycles`: false
  - `classifications_changed_after_first_cuts`: false (homogeneous)
- Same conclusion as K=6: the artefact family is large but uniform;
  CEGIS is structurally rigorous but combinatorially expensive.

## 2026-04-28 — Iteration 065 (artefact family analysis)

- New script `experiments/iteration_065_artifact_family_analysis.py`
  reads 063 proof_state JSONs and reports per-K family taxonomy.
- K=6 (300 rounds): 33 distinct cycle lengths (1-42), all denom < 0,
  |denom| from 19 to ~10^52.
- K=8 (50 rounds): 12 distinct cycle lengths (1-20), all denom < 0,
  |denom| from 65 to ~2 * 10^35.
- Both cleanly homogeneous: no REALIZABLE cycles, no zero-denom, no
  positive-denom-with-non-integer-fixed-point.

## 2026-04-28 — Iteration 066 (positivity-aware fuel)

- New module `verifiers/positivity_fuel.py` encodes the v_2-fuel
  lemma. For any periodic affine cycle with denom = 2^S - A and B
  from the canonical recurrence,

      T_pi(n) - a = A * (n - a) / 2^S
      eta_pi(n) := v_2(n * denom - B)             [equals v_2(n - a)
                                                  since denom is odd]
      eta_pi(T_pi(n)) = eta_pi(n) - S whenever T_pi(n) is integer.

  Hence the maximum number of integer T_pi-iterations from any n is
  exactly floor(eta_pi(n) / S).
- New experiment `experiments/iteration_066_positivity_fuel.py` runs
  this verification on every artefact cycle in the corpus (65 cycles
  drawn from 060c, 061, 062, 063 per-round logs):
    - v_2-fuel lemma holds: 63 / 63 (100 %; 2 skipped non-artefact).
    - parity-shadow <= v_2-fuel: 63 / 63 (always; consequence of the
      lemma).
    - parity-shadow strictly less than v_2-fuel: 12 / 63 (~19 %),
      reflecting that "orbit follows pi" is strictly stronger than
      "T_pi(n) is integer" — the orbit may break parity after fewer
      periods than v_2-fuel allows. The lemma is unaffected.
- LP-compatible recommendation: per-cycle Lyapunov term scaled by the
  cycle's total even-step count S_W, so each artefact-cycle period
  receives a finite v_2 fuel budget. This makes the LP positivity-
  aware: artefact cycles (denom < 0) are still admissible *finitely*
  rather than forcing infeasibility outright.

## 2026-04-28 — Iteration 067 (eta-fuel Lyapunov thresholds)

- New experiment `experiments/iteration_067_eta_fuel_thresholds.py`.
- For each artefact cycle in the corpus, compute the per-cycle
  Lyapunov threshold

      lambda_required(W) := drift(W) / S(W)

  using exact rational arithmetic (LOG2_3_UPPER) and find
  `lambda_max := max over witnesses of lambda_required`.
- Result on the 653 positive-drift artefact cycles drawn from 060c,
  061, 062, 063 per-round logs:
    - **lambda_max = 0.584962500721157 = LOG2_3_UPPER - 1** exactly.
    - Same value at K=6 (601 cycles) and K=8 (52 cycles).
    - All 653 cycles contract under `Phi(n) = log_2 n + lambda * eta`
      with `lambda = lambda_max + 0.01 = 0.5949625`.
- **Structural explanation.** Ordinary Collatz parity words have no
  two adjacent 1-bits (iteration 057's F_38 enumeration). Hence for
  any cycle, the maximum number of odd steps is `m <= T/2 + 1`, with
  `m = T/2` for even T (always true when K is even). Then
  `drift = m * log_2 3 - S` (algebraic identity using m+S=T) and
  `drift / S = (m/S) * log_2 3 - 1`. With `m = S` (the worst case
  under no-adjacent-1s, K even), `drift / S = log_2 3 - 1` exactly.
  This is a *universal* upper bound for ordinary Collatz artefact
  cycles at K even: the parity constraint pins the worst lambda.
- This is **cycle-level only**, not a global LP certificate. The
  question of whether a state-level psi compatible with this lambda
  exists is the next iteration (068).
- LP-compatible recommendation:
    - In the 060c LP, replace the per-edge depth term `c_val * lam[E2]`
      with a per-edge fuel term `S_per_window * lambda_global` where
      `lambda_global = log_2 3 - 1 + eps` is a fixed scalar (NOT a
      per-state variable).
    - This effectively pre-pays the v_2 fuel cost on every edge,
      collapsing the artefact-cycle Lyapunov check into the per-edge
      drift bound. If a state-level psi exists with this fixed lambda,
      we have a positivity-aware certificate.

## 2026-04-28 — Iteration 068 (fixed-lambda psi-only LP)

- New experiment `experiments/iteration_068_fixed_lambda_lp.py`.
- Replaces 060c's per-state `lam[E]` with a **single fixed scalar**
    `lambda_global = LOG2_3_UPPER - 1 + rho`,    `rho = 1e-6`.
- LP variables: psi[E] only (no lam). Per-edge constraint:
    psi[E2] - psi[E1] - lambda_global * S_edge <= -drift_edge - eps,
  equivalently
    psi[E2] - psi[E1] <= lambda_global * S_edge - drift_edge - eps.
- Sign convention: Phi(n) := log_2(n) + lambda * eta(n) + psi[state]
  drops by drift - lambda*S + (psi diff) per edge; with lambda > drift/S
  per 067, the cycle component is non-positive, so the LP encodes a
  Lyapunov potential.
- **K=6**: 19 519 states, 203 615 edges; **LP feasible** (HiGHS
  Optimal). min_margin = 0.0 (boundary), max_margin = 22.19.
  Total runtime 1.5 s.
- **K=8**: 535 168 states, 12 711 807 edges; **LP feasible** (HiGHS
  Optimal). min_margin = -1.78e-15 (floating-point boundary),
  max_margin = 31.70. Total runtime 190 s (69 s enum + 39 s build +
  81 s solve).
- This is the first **positivity-aware** feasibility result on the
  closed K=8 graph. NOT yet a Collatz proof: still need (a) exact
  rational re-verification (Iteration 069), (b) realised-trajectory
  closure, (c) scaling to larger K.

## 2026-04-28 — Iteration 069a (exact rational LP verifier)

- New experiment `experiments/iteration_069_audit.py` (combines 069a
  and 069b in one pass).
- Reads the saved psi from `certificates/iteration_068_certificate_K{K}
  .json`, converts to Fraction(p).limit_denominator(10**15), and
  verifies every edge constraint exactly:

      psi[E2] - psi[E1] - lambda_q * S_edge - drift_q <= 0

  with
      lambda_q  = LOG2_3_UPPER - 1 + Fraction(1, 10**6)
      drift_q   = m * (1 + LOG2_3_UPPER) - K
      LOG2_3_UPPER = Fraction(1584962500721157, 10**15).

  The LP padding `epsilon` is reduced to 0 in the verifier so the
  check is `<= 0` rather than `< -eps`; this absorbs the float-to-
  rational noise (~1e-15) that arises from psi rationalisation.
- **Results**:
  - **K=6**: 0 / 203 615 constraints failed; max violation 0.
    `verified_exact = true`.
  - **K=8**: 0 / 12 711 807 constraints failed; max violation 0.
    `verified_exact = true`. Verification runtime 219 s.
- This exactly verifies the iteration-068 LP certificate using
  rational arithmetic with the user-specified `LOG2_3_UPPER`. The
  feasibility statement is now ALGEBRAICALLY EXACT modulo the eps=0
  caveat; with strict eps > 0 the LP saturates the parity-induced
  upper bound on cycle drift/S, so any non-zero eps requires LP
  re-solving with corresponding rho.

## 2026-04-28 — Iteration 069b (semantic fuel audit)

- For each edge in the K=6 / K=8 closed graph, computes the per-fiber
  `c_val := delta_2 - delta_1` from a canonical witness fiber
  (`n_example`) and compares to the LP credit `-S_edge`.
- The credit -S_edge is *worst-case backed* (i.e. there exists a
  concrete fuel function with this drop on every fiber) iff
  `c_val_max <= -S_edge` for that edge.
- **Results**:
  - **K=6**: 11 874 / 203 615 = 5.8 % of edges are credit-backed
    worst-case.
  - **K=8**: 286 291 / 12 711 807 = 2.3 % of edges are credit-backed
    worst-case.
- The histogram of `(c_val_first + S_edge)` is heavily skewed toward
  positive (i.e. c_val > -S_edge) at both K's: peak at bucket 6 for
  K=8, bucket 4 for K=6.
- **Conclusion (matching the user's caveat)**: the iteration-068 LP
  is a *cycle-reweighted* feasibility certificate, NOT a per-edge
  Lyapunov potential. The credit -S_edge is correct on average
  (cycle-level, per 067) but NOT on every edge. A genuine descent
  Lyapunov requires a state-level eta(E, n) whose per-edge drop is
  >= S_edge for every (E, n); the existing per-window v_2 deltas do
  not satisfy this with the canonical fiber.

## 2026-04-28 — Iteration 070 (cycle-negativity interpretation)

- New experiment `experiments/iteration_070_cycle_negativity.py`.
- Theoretical equivalence (LP duality):

      LP (068) feasible <=> every directed cycle C in closed graph
      has total weight w(C) := sum_{e in C} (drift(e) - lambda*S(e))
      satisfying w(C) <= -|C|*eps.

  069a verified the LP exactly, so every directed cycle in the closed
  K=6 / K=8 graph has w(C) <= 0 exactly under
      lambda = LOG2_3_UPPER - 1 + 1e-6.
- Computational confirmation:
  - **K=6**: 11 self-loops; weight range [-3.17, -3.0e-06]. The
    binding self-loop has weight = -rho * S = -3e-06 (m=S=3 case).
    BF on -w(e) for 200 iterations finds NO positive cycle.
  - **K=8**: 26 self-loops; weight range [-6.34, -4.0e-06]. The
    binding self-loop has weight = -rho * S = -4e-06 (m=S=4 case).
    BF on -w(e) for 200 iterations finds NO positive cycle.
- The minimum self-loop weight (-rho * S) is the LP-saturating bound:
  it's exactly the per-edge slack provided by the rho padding.
- Random walks of length <= 12 didn't close (state space too large);
  closed-walk evidence is via BF only.
- **Status**: `exact_cycle_negativity_certificate_on_closed_K_graph`.
  Per-edge weights w(e) are real-valued; cycle sums are <= 0 exactly.
  This is strictly weaker than a Lyapunov descent certificate (per
  069b), but is a solid algebraic statement about the closed graph.
  Next step (Iteration 071+): lift the cycle-level certificate to a
  state-level descent function via flow / column-generation arguments,
  or formalise the cycle-negativity as a usable Collatz lemma.

## 2026-04-28 — Iteration 071A (LP dual decomposition)

- New experiment `experiments/iteration_071a_dual_decomposition.py`.
- Goal: extract the dual interpretation of the 068 fixed-lambda
  feasibility certificate; ask whether the certificate is equivalent
  to a pure difference potential or requires an augmented flow space.
- Findings at K=6:
  - With Phase-I objective `max sum(psi)` the LP is unbounded
    (psi can grow without bound subject to constraints), confirming
    the LP is "loose" with respect to anchored direction.
  - Falling back to zero objective: HiGHS returns a feasible psi
    with **min_margin = 0** at 1 258 / 203 615 = **0.6 %** of edges
    (tight edges).
  - The dual y is trivial (all-zero) under zero objective -- expected
    for feasibility-only LPs where the trivial circulation always
    satisfies Farkas.
  - Crucially: the **binding-edge subgraph contains 0 non-trivial
    SCCs and 0 binding self-loops**. Tight edges form a DAG-like
    skeleton; they never close into a cycle.
- Conclusion: the iteration-068 cycle-negativity is *strict* with
  rho-slack (no cycle is on the boundary). The certificate IS
  equivalent to a pure difference potential psi on the original
  state space; **no augmentation of the flow space is required**.
  The user's hypothesis ("equivalent to a pure difference potential
  on an augmented flow space") is confirmed in the *unaugmented*
  form.
- Take-home: 070 gave us cycle-negativity globally; 071A confirms
  this is strict (cycles are STRICTLY less than -|C|*eps),
  consistent with the algebraic identity drift / S = log_2 3 - 1
  versus lambda = log_2 3 - 1 + rho leaving rho per S unit of
  margin per edge.
- K=8 confirmation: 12 853 / 12 711 807 = 0.1 % tight edges,
  535 168 SCCs all trivial (size 1), 0 non-trivial SCCs, 0
  binding self-loops. Identical structural result as K=6.

## 2026-04-28 — Iteration 071B (realised-trajectory restriction)

- New experiment `experiments/iteration_071b_realized_trajectory.py`.
- For each fiber n0 traversing edge e, computes the *actual*
  per-window log_2 drift
      drift_actual(n) = log_2(T_pi(n) / n)
                      = drift_formula + log_2(1 + B_pi / (3^m * n)).
  drift_actual >= drift_formula always (B_pi > 0); excess is
  log_2(1 + B/(3^m * n)).
- Tests two questions:
  1. Does the 068 psi (built from formula drift) satisfy the
     *realised* LP `psi(E2) - psi(E1) <= lambda*S - drift_actual_max -
     eps`?
  2. Is the realised LP (using drift_actual_max per edge) feasible
     under any psi?
- **K=6 result**:
  - max excess (actual - formula) = 0.83 at small-n fibers
    (e.g. n=11 with K=6 cycle (40, 41) -> (4, 4)).
  - 39 327 / 203 615 = **19.3 % of edges violate 068's psi when using
    drift_actual_max**.
  - Excess histogram: 99.6 % of edges have excess < 0.01 (asymptotic
    regime); only ~81 edges have excess > 0.1 (the small-n
    breakers).
  - **Realised LP (re-solved) is INFEASIBLE** even with a fresh
    psi. The 81 high-excess edges form cycles whose actual drift
    exceeds the lambda*S budget.
- **Conclusion**:
  - 068's fixed-lambda certificate is an *asymptotic* / large-n
    statement; it doesn't survive worst-case realised drift on small
    n.
  - The small-n fibers (especially those visiting the trivial 1-2-4
    cycle's vicinity) introduce excess up to log_2(2) ≈ 1.0 per
    window. These break the constant-lambda structure.
  - The fixed-lambda LP is *not* a Lyapunov for actual integer
    dynamics; it's a Lyapunov for the asymptotic graph.
- Strongest current statement remains the closed-graph cycle-
  negativity certificate (070 + 071A); the realised-trajectory LP
  is genuinely tighter and demands a non-constant fuel structure.
- Path forward: either (a) bound small-n behavior separately via
  arbitrary-precision verification on small initial values, (b) add
  a state-dependent fuel correction term that absorbs the small-n
  log-bonus, or (c) restrict to large-n trajectories (n > some
  threshold N0) where excess is provably small.

## 2026-04-28 — Iteration 064 (positivity-domain theorem) — re-run

- New module `verifiers/positivity_theorem.py`. Encodes:

    THEOREM. For any T-step periodic ordinary-Collatz parity word
    with `m >= 1` odd bits and `S = T - m` even bits, let `A = 3^m`
    and `B` from the canonical recurrence. Then the affine fixed
    point `n_pi = B / (2^S - A)` is NOT a positive integer whenever
    the cycle has strictly positive total drift
    `Drift = m * (1 + log_2 3) - T > 0`, i.e. whenever `3^m > 2^S`.

    Proof. `Drift > 0  iff  3^m > 2^S  iff  2^S - 3^m < 0`. For
    `m >= 1` we have `B > 0` (every odd step injects `+ 2^S_at_step
    >= 1` and subsequent multiplications by 3 keep it positive).
    Therefore `n_pi = B / (2^S - 3^m) < 0`. If `B mod denom != 0`
    no integer fixed point exists at all. Either way `n_pi` is not
    a positive integer. QED.

- New experiment `experiments/iteration_064_positivity_theorem.py`
  applies `assert_positivity_theorem` to **every** cycle in the
  current witness corpus (060c, 061, 063 per-round summaries + 062
  classifications) and writes
  `proof_states/iteration_064_positivity_theorem.json`.
- **Result on 610 witness cycles**:
    - `drift_positive = 606`, `drift_negative = 4`, `drift_zero = 0`.
    - `theorem_consistent = 610 / 610` (100 %).
    - `non_positive_fixed_point = 610 / 610` (100 %).
    - `potentially_positive_int_fixed_point = 0`.
- Therefore: **every LP-infeasibility witness produced so far is a
  negative-domain artefact**, not a real Collatz cycle. The
  obstruction is structural to the (r, pi) abstraction.
- Implication: continuing to chip away at artefact cycles via CEGIS
  (063) is wasted effort. The right next move is a *positivity-aware*
  LP formulation that pre-filters or constrains the abstraction to
  the positive-integer domain (e.g. add `denom > 0` or
  `n_candidate > 0` as a cycle-level pre-condition rather than
  discovering its violations one cycle at a time).
