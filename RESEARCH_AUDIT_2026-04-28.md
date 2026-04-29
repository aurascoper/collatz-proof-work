# Deep Research Audit — Collatz Proof-Engineering Program

**Date**: 2026-04-28
**Scope**: Iterations 057–071 inclusive (notebook + experiments/ + proof_states/).

This document is **not** a Collatz proof and **not** an editorial endorsement of the
program; it is an adversarial audit of what is currently supported.

---

## Executive summary

The notebook has produced one solid, novel, computational artefact and one
clean negative bound on its applicability:

- **Solid result (068 + 069a + 070 + 071A)**: the closed K=8 directed graph
  whose vertices are 2-window edge-states (`r1, π0, r2, π1`) and whose
  edges are realised by integers in `[1, 2³ᴷ)` admits an exact-rational
  difference potential `ψ` such that
  `ψ(E₂) − ψ(E₁) − λ·S(e) ≤ −drift(e) − ε`
  with `λ = LOG2_3_UPPER − 1 + 10⁻⁶` and `LOG2_3_UPPER =
  Fraction(1584962500721157, 10¹⁵)`. Equivalently every directed cycle has
  weight `<−|C|·ε` exactly. Verified on 12,711,807 edges with 0 / 12.7M
  failures.

- **Clean negative bound (069b + 071B)**: that certificate is **not** a
  Lyapunov on actual positive integers. Per-edge fuel realisation is
  backed in worst case by only 5.8 % (K=6) / 2.3 % (K=8) of edges (069b),
  and replacing formula drift by worst-case actual drift makes the LP
  **infeasible** at both K=6 (excess 0.83 at small n) and K=8 (excess
  1.245). The `λ·S` term is a cycle-level reweighting, not a state Lyapunov.

The strongest **mathematically correct** statement is therefore a
*finite-graph* theorem about the (r,π) abstraction, **strictly weaker** than
existing Collatz cycle-exclusion results (Hercher 2022 already proves
that no non-trivial Collatz cycle exists with at most 91 odd elements).
The LP framework, **in its present form, is not on a path to a full
Collatz proof**: the formula-drift vs actual-drift gap reappears at
every K and is incompatible with a state-level Lyapunov bound under
any single λ (this is a research-judgment about *this approach*,
not a meta-mathematical certainty about Collatz).

---

## A. Iteration audit table

Status legend:
- **EXACT**: holds in rational arithmetic; verifiable with `Fraction` + `LOG2_3_UPPER`.
- **CLOSED-SYM**: holds on a fully enumerated graph (`n0 mod 2^{3K}`) but uses
  formula drift, not actual integer drift.
- **SAMPLED**: relies on random / partial sampling; not universal.
- **HEURISTIC**: structural reasoning; not formally a theorem.
- **INVALIDATED**: superseded by a later iteration's correction.
- **DIAGNOSTIC**: a method, not a claim.

| Iter | Title                                  | Status                | Result / Caveat |
|------|----------------------------------------|-----------------------|-----------------|
| 057  | F₃₈ admissible parity-word count       | EXACT                 | 39,088,169 length-36 ordinary-Collatz parity words (Fibonacci F₃₈). Standard combinatorial fact. |
| 058  | Closed parity-overlap LP K=12          | CLOSED-SYM, INVALIDATED | LP infeasible; abstraction is parity-overlap proxy, not affine residue. |
| 059  | K=6 affine harness                     | EXACT                 | Per-window affine constants verified against simulation. |
| 060a | K=8 c_val-split affine LP              | CLOSED-SYM            | LP infeasible. |
| 060b | K=8 cycle witness                      | CLOSED-SYM            | Length-4 cycle, non-realisable (negative-domain). |
| 060c | K=8 c_val-split (cleaned)              | CLOSED-SYM            | LP infeasible. c_val-split fanout: only 0.11 % vs `c_max`. |
| 060d | Self-loop artefact filter              | CLOSED-SYM            | K=6: 3/11 realisable; K=8: 0/26. Filtering self-loops alone is insufficient. |
| 061  | 3-window state encoding                | SAMPLED               | 5 M seeds → feasible (boundary). 10 M seeds → infeasible. **Sampling-flip**, not a theorem. |
| 062  | Cycle admissibility classifier         | EXACT (verifier)      | Composes affine map, solves `(2^S − 3^m)·n = B`, validates by simulation. 0 / 5 realisable in original corpus. |
| 063  | Artefact-aware CEGIS                   | DIAGNOSTIC            | K=6/300r and K=8/50r both: 100 % artefact cycles cut, LP still infeasible (combinatorially many). |
| 064  | Positivity-domain theorem              | EXACT                 | `drift > 0  ⇔  3^m > 2^S  ⇔  denom < 0  ⇒  n_pi ≤ 0`. 660/660 corpus consistent. **This is the structural backbone**. |
| 065  | Artefact family analysis               | DIAGNOSTIC            | K=6 has 33 distinct cycle-lengths in artefacts (\|denom\| 19→10⁵²); K=8 has 12 (65→2·10³⁵). Pure structure. |
| 066  | v₂-fuel lemma                          | EXACT                 | `η_pi(T_pi(n)) = η_pi(n) − S` whenever T_pi(n) is integer; verified arithmetically on 63/63 artefact cycles. |
| 067  | Universal λ threshold                  | EXACT                 | `λ_max = LOG2_3_UPPER − 1` over 653 artefact cycles. Pinned by the no-adjacent-1s parity constraint (m ≤ S for even T). |
| 068  | Fixed-λ ψ-only LP                      | CLOSED-SYM            | **K=6 and K=8 feasible** under HiGHS at floating-point precision; min-margin ≈ 0 (boundary). Independently verified exact-rational with 0/12,711,807 constraint failures (Iteration 069a). |
| 069a | Exact rational LP verifier             | **EXACT**             | **0 / 12,711,807 failures at K=8** with `eps_q = 0`. ψ certificate is algebraically valid. |
| 069b | Semantic fuel audit                    | EXACT (negative)      | K=8: only 2.3 % of edges have credit-backed worst-case `c_val ≤ −S_edge`. The credit is **not** a per-edge Lyapunov. |
| 070  | Cycle-negativity interpretation        | EXACT                 | By LP duality, every directed cycle in the *reweighted* closed K=6/K=8 graph has `w(C) ≤ −|C|·ε` exactly (this is a statement about the reweighted abstract graph, not the underlying integer dynamics). Equivalent to 068 + 069a. |
| 071A | LP dual decomposition                  | EXACT                 | Tight edges form a DAG (0 non-trivial SCCs); cycle-negativity is **strict** with ρ-slack; ψ is a pure difference potential, no augmentation. |
| 071B | Realised-trajectory restriction        | EXACT (negative)      | Replacing formula drift by worst-case actual drift: K=6 → 19.3 % violations, **realised-LP infeasible**. K=8 → 2.66 % violations, max excess 1.245. The fixed-λ certificate is asymptotic, not real. |

---

## B. Literature comparison

### Standard / well-known constructions used in the notebook

- **Parity-vector encoding** (Terras 1976 *A stopping time problem on the
  positive integers*; Lagarias 1985 *The 3x+1 problem*): the first K
  parity bits of an integer `n` uniquely determine `n mod 2^K`. The
  notebook uses this implicitly. Standard.
- **No-adjacent-1s in ordinary Collatz**: after an odd step, `3n+1` is
  even, so the next step is forced even. Yields Fibonacci counting of
  admissible parity words. Standard textbook fact (e.g. Lagarias survey).
- **Drift constant `log₂ 3 − 1`**: appears in dozens of Collatz papers
  as the per-step log-growth in the "alternating" regime. Equivalent to
  saying compressed Collatz `T₂(n) = (3n+1)/2 if odd` has expected
  log-growth `½(log₂ 3 − 1) − ½ = (log₂ 3 − 2)/2 ≈ −0.21` (negative,
  hence "decreasing on average").
- **Korec's constant `log(3)/log(4) ≈ 0.7924`** appears in
  `Col_min(N) ≤ N^θ` for almost all N (cited in Tao 2019). This is a
  **different** constant from λ in this notebook; do not conflate.

### Notebook-novel computational contributions

- **Iteration 069a**: exact rational verification of an LP feasibility
  certificate at K=8 with 12.7M constraints. We are not aware of prior
  Collatz papers exhibiting an exactly-verified state potential at this
  scale.
- **Iteration 067**: structurally derives `λ_max = log₂ 3 − 1` from the
  no-adjacent-1s parity constraint, rather than fitting it from the LP.
  This is a small but clean observation.
- **Iterations 070 + 071A**: identify the certificate as a *cycle-
  negativity* statement on the closed graph and confirm via primal
  binding-edge subgraph analysis that the certificate is realised by a
  pure difference potential (no flow-space augmentation).

### Strictly stronger existing results

- **Tao 2019** (arXiv:1909.03562): for any function `f(N) → ∞`,
  `Col_min(N) ≤ f(N)` for almost all N (logarithmic density). Probabilistic
  / 3-adic skew random walk. Proves a vastly stronger almost-everywhere
  statement than anything in the notebook.
- **Korec 1994** (cited in Tao 2019): `Col_min(N) ≤ N^θ` for any
  θ > log(3)/log(4), almost all N. Stopping-time / probabilistic.
- **Hercher 2022** (arXiv:2201.00406): every non-trivial Collatz cycle
  must have at least m = 92 odd elements (in the parity-vector sense
  — equivalent to "odd steps" in the standard parity vector but
  phrased in the source paper as "odd elements"/"rises"). Uses
  Baker bounds on linear forms
  in logarithms and continued-fraction approximations of `log 3 / log 2`.
  This is a **rigorous cycle-exclusion theorem** applicable to all
  positive integers; the notebook only verifies the parity bound at K ≤
  8, which is much weaker.
- **Eliahou 1993**, **Krasikov–Lagarias 2003**: continued-fraction /
  logarithmic-form cycle exclusion. Established framework.

### Other recent attempts in the literature

- **Yolcu, Aaronson, Heule 2021** (arXiv:2105.14697): string-rewriting
  termination view; finds automated proofs for Collatz weakenings but not
  the conjecture. Methodologically related to the notebook in spirit.
- **Gonçalves, Greenfeld, Madrid 2021** (arXiv:2111.06170): generalises
  Tao to (p,q) Collatz-like maps.
- **Mori 2024** (arXiv:2411.08084): C\*-algebra / Cuntz-algebra
  reformulations. Equivalences but no breakthrough.
- **Paparella 2024** (arXiv:2406.08498): equivalence to nilpotency of
  certain matrices.
- **Various math.GM submissions** (e.g. arXiv:2008.13643, 1208.2556,
  2209.13541): claim full proofs but are not refereed; treat as
  unverified.

### Where the notebook sits

| Method                 | Cycle exclusion | Almost-bounded orbits |
|------------------------|-----------------|-----------------------|
| Tao 2019               | —               | yes, log-density       |
| Hercher 2022           | m ≥ 92           | —                     |
| Eliahou / Krasikov     | weaker bound m  | —                     |
| Notebook 068+069a+070  | none new (only K ≤ 8 finite-graph cycle-negativity) | — |

The notebook does not improve on any existing rigorous Collatz theorem.

---

## C. Can the fixed-λ certificate be upgraded to a state-level theorem?

### C1. Is there a state functional η with `Δ(log₂ n + ψ + λ·η) ≤ −ε` on
realised trajectories?

**Conditional answer: NO in this framework**.

- The v₂-fuel `η_pi(n) = v₂(n*denom − B_pi)` decreases by exactly `S`
  per `T_pi`-integer-iteration (Iteration 066 lemma).
- However, the per-window v₂-delta `c_val = δ₂ − δ₁` used in
  Iterations 060c/068 changes between adjacent edges, and the per-edge
  drop is generally NOT `−S` (Iteration 069b: 97.7 % of edges at K=8
  have `c_val_max > −S_edge`).
- A genuine `η(E, n)` with the required per-edge property would have to
  encode `n − a_pi(E)` consistently across consecutive π_i with different
  fixed points `a_πᵢ`, but the fixed points themselves drift between
  windows. There is no canonical such η visible in the data.
- Iteration 071B confirms operationally: replacing formula drift with
  worst-case actual drift makes the LP infeasible, so no fresh `ψ` works
  on the realised graph at fixed λ.

### C2. Is the certificate naturally a flow / cycle certificate?

**Yes, this is its actual content.**

By LP duality, 068's feasibility is exactly the statement "every directed
cycle has total weight `≤ −|C|·ε`" (Iteration 070). 071A confirms the
binding edges form a DAG, so the cycle-negativity is *strict* (with
ρ-slack on every cycle, not boundary-binding).

This means the certificate carries cycle-level information but does not
upgrade to per-edge / per-state descent.

### C3. Is there a known framework that lifts cycle negativity to descent?

Three candidates:

1. **Karp's min-mean-cycle theorem**: characterises the minimum mean
   weight of any cycle in a digraph. Not a Lyapunov; only a bound.
2. **Linear potential lifting** in graph theory: Bellman-Ford produces a
   state potential ψ when no negative cycle exists; this is exactly what
   we have. It does not produce a Lyapunov on a *path*, only acyclicity-
   like properties on cycles.
3. **Ergodic / Birkhoff averages** (e.g. Santana 2026 arXiv:2601.03297):
   for thermodynamic-formalism approaches, "recurrence implies
   periodicity" can be made rigorous, but does not give per-orbit descent.

None of these directly upgrades a cycle certificate to a Lyapunov.

---

## D. Positivity-restricted quotient — can we construct one?

**Yes, but it does not solve the descent problem.**

The construction:

- **Vertices**: same as the closed K-graph: 2-window edge-states.
- **Edges**: only those `(E₁, E₂)` such that there exists a positive
  integer `n` traversing it. Iteration 060c / 060d already has this:
  every enumerated edge is realised by some `n₀ ∈ [1, 2^{3K})`.
- **Cycle filter**: drop every cycle `C` whose composed affine map has
  `denom = 2^S − 3^m ≤ 0`, OR whose `B / denom` is non-positive.

This quotient is well-defined and computable (Iteration 062 classifier).
At K=8 the filter removes a vast artefact family (Iteration 065:
millions of distinct cycle classes).

**However**, the realised-trajectory LP on this quotient is **still
infeasible** by the same mechanism as 071B: the actual drift on small-n
fibers exceeds the formula drift, and this excess accumulates around any
cycle that intersects small-n trajectories.

So the missing invariant is not the artefact filter (which we already
have) but a state functional sensitive to `log₂(1 + B_pi/(3^m·n))`.
This term depends explicitly on `n`, not just on the (r, π) abstract
state.

**Negative conclusion**: any abstraction blind to the `n` value cannot
absorb the small-n excess. The notebook's framework is fundamentally an
abstract-state framework. The descent gap is not in the LP — it's in the
state encoding.

---

## E. Concrete next-step design

**Recommended path: PATH 4-prime — pivot to logarithmic-form / Diophantine
cycle exclusion using the notebook's enumeration as input data.**

**Why not the other three paths**:
- **Path 1 (071B)** done; result: realised-LP infeasible. No further
  iteration of the same idea will succeed.
- **Path 2 (column generation)** — would only re-package the same cycle
  certificate; doesn't address the formula/actual gap.
- **Path 3 (larger K)** — the K=10 / K=12 graphs scale 64× / 4096× edge
  count. The same closed-graph cycle-negativity certificate would hold
  with the same λ (per 067 the bound is structural, not K-dependent),
  but realised-trajectory LP would be just as infeasible.

### Path 4-prime: Hercher-style cycle exclusion + notebook enumeration

**Statement of intent**: rather than upgrade the LP, switch to the
Diophantine framework that has already produced rigorous Collatz cycle
bounds (Hercher 2022; Eliahou 1993; Krasikov–Lagarias).

**Approach**: for each candidate cycle parity word `π = (π_1, …, π_L)`
in the notebook's enumeration:

1. Compute `A = 3^m`, `B`, `S = T − m` exactly.
2. Compute `n_candidate = B / (2^S − A)` if it is a positive integer;
   otherwise the cycle is excluded structurally.
3. For surviving candidates (positive integer `n`), apply the linear-
   forms-in-logarithms bound:
   `|m·log 3 − S·log 2| ≥ c · max(m, S)^{−κ}`
   with explicit constants from de Bruijn–Mignotte / Rhin / Laurent.
4. Show that for any such candidate cycle below the verified Collatz
   bound (`N₀ ≈ 2⁶⁸` per Roosendaal), simulation reaches 1 in finitely
   many steps — directly contradicting cyclicity.

This gives a hybrid theorem:
- **Computational**: enumerate candidate parity words at K up to some
  bound, classify by 062.
- **Symbolic**: for each surviving (positive-integer-realisable) candidate,
  derive a Baker-style lower bound on `|m·log 3 − S·log 2|`.
- **Boundary verification**: certify Collatz directly for `n ≤ N₀` via
  arbitrary-precision simulation.

### Pseudocode for an Iteration 072

```python
# Iteration 072: hybrid Diophantine cycle exclusion
from fractions import Fraction
from sympy.ntheory import baker_bound  # or hand-coded explicit Baker bound

LOG2_3_UPPER = Fraction(1584962500721157, 10**15)
N0_VERIFIED = 2**68  # Roosendaal's verified bound (or current best)

def classify_and_exclude(pi_middles_seq, K):
    A, B, S = compose_affine(pi_middles_seq, K)
    denom = (1 << S) - A
    if denom <= 0 or B % denom != 0:
        return "non_realisable_artefact"
    n = B // denom
    if n <= 0:
        return "non_realisable_artefact"
    if n <= N0_VERIFIED:
        # Direct verification
        actual_traj = simulate_collatz(n, max_steps=10000)
        if actual_traj[-1] == 1:
            return "verified_descent_to_1_no_cycle_through_this_n"
        else:
            return "REALIZABLE_CANDIDATE_CYCLE_RAISE_ALERT"
    # n > N0_VERIFIED: apply Baker-Hercher bound
    L = len(pi_middles_seq)
    m_total = popcount_sum(pi_middles_seq)
    if hercher_lower_bound(m_total, S) > 0:
        return "excluded_by_baker_bound"
    # surviving candidates: parity word survives both filters
    return "open_candidate_requires_finer_analysis"

# Pipeline
for L in range(1, MAX_LENGTH):
    for pi_seq in enumerate_admissible_parity_seqs(L, K):
        verdict = classify_and_exclude(pi_seq, K)
        log[verdict].append(pi_seq)
```

### Proof obligations for Path 4-prime

1. **Baker bound applicability**: confirm with explicit constants that
   for any cycle with `m ≤ M_max` (manageable enumeration bound), the
   Baker lower bound gives `|m·log 3 − S·log 2| ≥ ε(m, S)` strong enough
   to rule out a non-trivial integer fixed point with positive `n`.
2. **Coverage**: enumerate all admissible parity sequences up to length
   `L_max` such that any non-trivial cycle of length ≤ `L_max` is captured.
3. **Boundary join**: ensure `N₀_VERIFIED` is large enough that no
   candidate cycle has a fixed point in `(0, N₀_VERIFIED]` un-verified.

This path makes contact with the existing literature (Hercher, Eliahou)
and is the most likely to produce a *new* rigorous result — but it is
not Lyapunov-based and does not extend the LP framework. **The honest
conclusion is: the LP framework as constructed is essentially closed.**

---

## F. Failure modes

1. **The closed-graph cycle-negativity certificate is genuine but
   "small"**: it is a structural fact about a specific finite directed
   graph at K ≤ 8, strictly weaker than every existing rigorous Collatz
   result. Trying to scale it to K = 10/12/16 will succeed (same proof)
   but will not produce new content.

2. **Realised-trajectory LP cannot be made feasible** with a constant
   global λ. Iteration 071B gave the proof: small-n fibers (especially
   those visiting the trivial 1–2–4 cycle's vicinity) inject excess up
   to log₂(2) ≈ 1 per window, breaking the structure.

3. **State augmentation does not obviously help**: the natural
   augmentations (η = v₂-fuel, current `n` value, distance from affine
   fixed point) either drop unevenly per edge (Iteration 069b) or carry
   information that the formula-drift LP cannot price in a state-only way.

4. **A "proof" through this framework would require novel ingredients
   not currently in the notebook**: e.g. a Baker bound (Diophantine
   number theory, Hercher framework) or a probabilistic argument
   (Tao framework). Neither is computational LP.

5. **Two paths that genuinely could yield publishable contributions**
   from this work:
   - The structural derivation of `λ = log₂ 3 − 1` from no-adjacent-1s
     (Iteration 067) is a clean small theorem, possibly novel as written.
   - The exact rational LP verification at K=8 (Iteration 069a) is a
     rare computational artefact at this scale; useful as a test bed
     for future automated-proof tooling (cf. Yolcu–Aaronson–Heule 2021).
   Neither is a Collatz proof; both are honest contributions.

---

## Citations

- Tao, T. (2019). "Almost all orbits of the Collatz map attain almost
  bounded values." arXiv:1909.03562. https://arxiv.org/abs/1909.03562
- Korec, I. (1994). "A density estimate for the 3x+1 problem."
  *Mathematica Slovaca* 44(1).
- Lagarias, J.C. (1985). "The 3x+1 problem and its generalizations."
  *American Mathematical Monthly* 92, 3–23.
- Terras, R. (1976). "A stopping time problem on the positive integers."
  *Acta Arithmetica* 30, 241–252.
- Hercher, C. (2022). "There are no Collatz-m-Cycles with m ≤ 91."
  arXiv:2201.00406. https://arxiv.org/abs/2201.00406
- Eliahou, S. (1993). "The 3x+1 problem: new lower bounds on nontrivial
  cycle lengths." *Discrete Mathematics* 118, 45–56.
- Krasikov, I., Lagarias, J.C. (2003). "Bounds for the 3x+1 problem
  using difference inequalities." *Acta Arithmetica* 109, 237–258.
- Yolcu, E., Aaronson, S., Heule, M.J.H. (2021). "An Automated Approach
  to the Collatz Conjecture." arXiv:2105.14697. https://arxiv.org/abs/2105.14697
- Gonçalves, F., Greenfeld, R., Madrid, J. (2021). "Generalized Collatz
  Maps with Almost Bounded Orbits." arXiv:2111.06170. https://arxiv.org/abs/2111.06170
- Roosendaal, E. (ongoing). "On the 3x+1 problem." Computational
  verification database. http://www.ericr.nl/wondrous/
- Mori, T. (2024). "Application of Operator Theory for the Collatz
  Conjecture." arXiv:2411.08084.
- Paparella, P. (2024). "A matricial view of the Collatz conjecture."
  arXiv:2406.08498.
- Santana, E. (2026). "On the Collatz Conjecture: Topological and
  Ergodic Approach." arXiv:2601.03297.

(All `arXiv` IDs were retrieved on 2026-04-28 via the local arxiv MCP
server. The math.GM submissions claiming full Collatz proofs
(arXiv:2008.13643, 1208.2556, 2209.13541, 2305.10117) are listed for
completeness but treated as unverified per arXiv policy.)
