# Editorial review and consistency audit

**Reviewer role**: skeptical mathematical editor and consistency auditor
(not coauthor).
**Date**: 2026-04-28.
**Scope**: the full body of `collatz-proof-work` materials treated as
one preprint — `RESEARCH_AUDIT_2026-04-28.md`,
`cycle_exclusion_engine/NOTE_periodic_word_engine.md`,
`iteration_077_diophantine_handoff_DESIGN.md`, `changelog.md`,
`README.md`, the iteration `proof_states/`.
**Deliverables**: (1) editorial revision skeleton; (2) consistency
audit with overclaim, notation, and citation findings; (3) final
red/yellow/green assessment.

This document does **not** rewrite the preprint inline. It produces the
title/abstract/introduction/section-ordering/contributions/limitations
that the preprint should adopt, plus an audit log of overclaim risks,
notation drift, and citation wording that should be sharpened or
softened before submission. No new mathematical claim is introduced.

---

# PASS 1 — Editorial revision

## 1. Revised title

> **Closed-graph cycle-negativity at K = 8 and primitive periodic-word
> exclusion through T ≤ 36 for the ordinary Collatz map: two
> computational artefacts**

Rationale: states the two artefacts explicitly with their scopes; does
not promise more than is delivered; avoids the words "proof",
"theorem", "Lyapunov", and "descent" in the title.

## 2. Revised abstract

> We report two distinct computational artefacts on the ordinary
> Collatz map and discuss what each does and does not establish.
>
> **Branch I (closed-graph LP).** On a fully enumerated 2-window
> edge-state graph at `K = 8` (535,168 states; 12,711,807 edges
> realised by integers in `[1, 2^{3K})`), we exhibit a difference
> potential `ψ : States → Q` such that for every edge `e = (E₁, E₂)`
> of the graph,
>
>     ψ(E₂) − ψ(E₁) − λ·S(e) ≤ −drift(e) − ε,
>
> with `λ = LOG2_3_UPPER − 1 + 10⁻⁶`,
> `LOG2_3_UPPER = Fraction(1584962500721157, 10¹⁵)`,
> `drift(e) = m_middle·(1 + log_2 3) − K`, and `S(e) = K − m_middle`.
> The certificate is verified by exact rational arithmetic on every
> one of the 12.7 M edges. By LP duality, every directed cycle in
> this graph has weight `≤ −|C|·ε`. We refer to this as a
> *closed-graph cycle-negativity certificate*. We do **not** claim
> a Lyapunov descent statement on positive-integer trajectories;
> a per-edge fuel audit shows the cycle-level credit is backed in
> worst case by only ~2.3 % of edges at `K = 8`, and replacing
> formula drift by worst-case actual drift makes the LP infeasible.
>
> **Branch II (primitive periodic-word exclusion engine).** A
> two-language pipeline (Rust generator + Julia exact classifier
> with theorem dispatcher) enumerates every primitive cyclically-
> admissible periodic parity word of bounded length `T`, composes
> its exact `BigInt` affine map, classifies the algebraic fixed
> point, and dispatches surviving candidates through a theorem
> layer importing Hercher 2022's `m ≥ 92` lower bound and a
> trusted finite-verification ceiling. Through `T ≤ 36`
> (2,552,323 primitive words; 327 s end-to-end), the engine
> produces exactly one realisable class — the trivial 1–4–2 cycle
> in canonical form "001" — and zero non-trivial or open
> candidates. A `T ≤ 48` attempt is **disk-limited; deferred**:
> the NDJSON transport reached ~6.4 GB before completing, an
> engineering limit, not a mathematical one.
>
> Neither artefact is a proof of the Collatz conjecture. Branch I
> is strictly weaker than existing rigorous cycle-exclusion
> results (Hercher 2022); Branch II reproduces a corollary of the
> same literature with auditable provenance. We document the
> framework's limits explicitly and define a sequel iteration
> (077) for an explicit linear-forms-in-logarithms handoff.

## 3. Revised introduction (skeleton)

```
§1 Introduction
   §1.1 What the paper claims and what it does not
        — two computational artefacts; not a Collatz proof
        — claim discipline: EXACT / CLOSED-SYM / SAMPLED /
          DIAGNOSTIC / INVALIDATED
        — relation to Tao 2019, Hercher 2022, Eliahou 1993,
          Krasikov-Lagarias 2003, Lagarias 1985, Terras 1976
   §1.2 Why two branches
        — Branch I addresses the (r, π) abstraction and its
          intrinsic LP feasibility under a fixed parity-induced λ.
        — Branch II addresses periodic-word cycle candidates
          directly and is intended as a Diophantine front end.
   §1.3 Reproducibility and provenance
        — exact rational arithmetic via Python `Fraction`
          (Branch I) and Julia `BigInt` (Branch II).
        — every theorem-based exclusion records source, version,
          threshold, and numeric gap.
```

## 4. Cleaned section ordering

```
§1 Introduction                                  (above)
§2 Notation, status categories, and conventions
   §2.1 Ordinary Collatz parity vector and the no-adjacent-1s rule
   §2.2 Notation: K, T, m, S, drift, λ, ψ, A, B, denom, η
   §2.3 Status categories: EXACT / CLOSED-SYM / SAMPLED / DIAGNOSTIC
                         / INVALIDATED
   §2.4 Reproducibility convention (LOG2_3_UPPER, ε, ρ values)

§3 Branch I — closed-graph cycle-negativity at K=8
   §3.1 Setup: edge-states E = (r₁, π₀, r₂, π₁) at K=8
   §3.2 Iteration timeline 060c → 061 → 062 → 063 → 064 → 065 → 066 → 067
   §3.3 Iteration 068: fixed-λ ψ-only LP and floating-point feasibility
   §3.4 Iteration 069a: exact rational verification (0/12.7M failures)
   §3.5 Iteration 070: LP-dual cycle-negativity interpretation
   §3.6 Iteration 071A: binding-edge subgraph is acyclic (DAG)
   §3.7 Iteration 069b: per-edge fuel audit (NEGATIVE finding)
   §3.8 Iteration 071B: realised-trajectory restriction (NEGATIVE finding)
   §3.9 Branch I closure: what the certificate is, and what it is not

§4 Branch II — primitive periodic-word exclusion engine
   §4.1 Mathematical object
   §4.2 Architecture (Rust + Julia, NDJSON v2 schema)
   §4.3 Iteration 072: primitive cyclic-admissible enumeration + affine
                        composition (with cross-checks against direct
                        Collatz simulation)
   §4.4 Iteration 072.5: theorem dispatcher (finite verification +
                          Hercher m ≥ 92)
   §4.5 Iteration 072.6: candidate analyzer (Δ ranking, CF convergents)
   §4.6 Results: T ≤ 12, T ≤ 24, T ≤ 36 classification tables
   §4.7 Iteration 073/074 verification reproductions
   §4.8 Iteration 075: T ≤ 48 attempt — DISK-LIMITED; DEFERRED

§5 Comparison with the existing Collatz literature
   §5.1 Cycle-exclusion line: Eliahou, Krasikov-Lagarias, Hercher
   §5.2 Almost-bounded orbits: Tao 2019
   §5.3 Where this work sits

§6 Limitations and non-claims (FULL SECTION; see §7 below)

§7 Future work: Iteration 077 (Diophantine handoff)

§8 References
```

## 5. Main contributions

The preprint should claim exactly the following — no more, no less.

1. **Branch I, exact rational LP feasibility.** A fixed-λ ψ-only
   LP is exactly feasible on the closed `K = 8` 2-window edge-
   state graph (12,711,807 edges) under exact rational arithmetic
   with `LOG2_3_UPPER = Fraction(1584962500721157, 10¹⁵)`. The
   universal constant `λ = LOG2_3_UPPER − 1 + 10⁻⁶` is derived
   structurally from the no-adjacent-odd-bits parity constraint of
   ordinary Collatz, not fitted from the LP.
   **Status**: EXACT.

2. **Branch I, cycle-negativity interpretation.** By LP duality
   the certificate of (1) is equivalent to the statement that
   every directed cycle in the closed `K = 8` graph has total
   reweighted weight `≤ −|C|·ε` (in fact strictly less, with
   ρ-slack, because the binding subgraph is a DAG).
   **Status**: EXACT.

3. **Branch I, semantic-gap diagnostic.** The certificate is
   *not* a Lyapunov descent statement on positive integers: the
   per-edge "credit" `−λ·S(e)` is backed in worst case by only
   5.8 % of edges at `K = 6` and 2.3 % at `K = 8`, and replacing
   formula drift by worst-case actual drift renders the LP
   infeasible.
   **Status**: EXACT (negative).

4. **Branch II, periodic-word exclusion through T ≤ 36.** A
   reproducible two-language pipeline classifies all 2,552,323
   primitive cyclically-admissible periodic parity words of length
   ≤ 36 under exact `BigInt` arithmetic. Through `T ≤ 36`, the
   only realisable class is the trivial 1–4–2 cycle (canonical
   word "001", `n = 4`); no non-trivial or open candidate
   appears.
   **Status**: EXACT (in the scanned range).

5. **Branch II, theorem-provenance scaffolding.** Each non-
   structural exclusion records its theorem source by reference
   (Hercher 2022 for the `m ≥ 92` bound; Roosendaal-class verified
   bound for the finite-verification layer). The pipeline never
   re-derives these theorems and never silently excludes a
   candidate.
   **Status**: EXACT engineering scaffolding around imported
   theorems.

6. **Negative scaling result (engineering, not math).** A `T ≤ 48`
   scan was attempted with the same NDJSON pipeline and aborted
   when the output approached 6.4 GB. This is an engineering limit
   on the chosen transport, not a mathematical statement; we
   record it as DISK-LIMITED; DEFERRED.
   **Status**: DIAGNOSTIC (engineering).

## 6. Limitations and non-claims (full section text)

> The following are **explicit non-claims** of the present work.
>
> 1. We do not prove the Collatz conjecture, nor any partial result
>    that is not already supplied by the cited literature
>    (Hercher 2022; Tao 2019; Eliahou 1993; Krasikov–Lagarias 2003;
>    Lagarias 1985).
>
> 2. The Branch I certificate is a statement about a specific
>    finite directed graph derived from `n₀ mod 2^{3K}` at
>    `K = 8`. It is *not* a statement about the Collatz dynamics
>    on positive integers. The semantic-gap diagnostic (§3.7,
>    §3.8) is part of the result, not a footnote.
>
> 3. The Branch I `−λ·S` reweighting is a *cycle-level
>    correction*. By a per-edge fuel audit and a realised-
>    trajectory LP re-solve, it is *not* a per-edge Lyapunov
>    descent term on positive integers.
>
> 4. The Branch II engine is an *exclusion engine*. It does not
>    re-prove the Hercher `m ≥ 92` bound, nor the trusted finite-
>    verification bound (Roosendaal-class). Both are imported by
>    reference, with full provenance recorded in every relevant
>    verdict.
>
> 5. The Branch II `T ≤ 48` row is **disk-limited; deferred**. It
>    is not a partial mathematical exclusion; it is an aborted
>    engineering attempt. The strongest defensible Branch II
>    claim remains at `T ≤ 36`.
>
> 6. The Branch II analyzer (Iteration 072.6) ranks candidates by
>    `Δ = |m·log 3 − S·log 2|`. This is a diagnostic ranking, not
>    an exclusion mechanism. It cannot exclude any candidate by
>    itself.
>
> 7. The Iteration 077 design is a design document; it does not
>    yet implement an explicit linear-forms-in-logarithms
>    exclusion. No verdict produced from any current artefact in
>    this work depends on 077.
>
> 8. We make no claim about non-cyclic divergent orbits. Tao 2019
>    is the relevant landmark for almost-all-orbit statements; we
>    do not extend or strengthen it.

## 7. Sentences that risk overclaiming

The following phrases (verbatim or near-verbatim) appear in the
existing artefacts and should be revised in the editorial pass.
Severity: **R** = red (must change), **Y** = yellow (sharpen).

- (Y) `RESEARCH_AUDIT §A` row 070: *"every directed cycle has
  weight ≤ 0 exactly"*. Add the qualifier *"by LP duality"* and
  state explicitly that this is in the reweighted graph, not in
  the underlying integer dynamics.

- (Y) `changelog.md` 068 entry: *"first positivity-aware
  feasibility result on the closed K=8 graph"*. The phrase
  "positivity-aware" is acceptable only because it is defined
  earlier; otherwise read as marketing. Clarify on first use.

- (R) `changelog.md` 073 entry: *"only the trivial 1-2-4 cycle
  survives at T <= 36"*. Should read: *"only the trivial 1–4–2
  cycle is realised among the primitive cyclically-admissible
  periodic words of length T ≤ 36"*. As written, the phrase
  invites the reader to infer "no non-trivial cycle exists at
  T ≤ 36 in Collatz", which is unsupported.

- (Y) `NOTE_periodic_word_engine.md` §4.5 summary block: *"the
  engine finds exactly one realisable class … and zero non-
  trivial realisable or open candidates."* Acceptable, but should
  say *"in the scanned range"* explicitly within the same
  sentence rather than only in the surrounding prose.

- (R) `RESEARCH_AUDIT.md` Section A row "060c K=8":
  *"K=8 fixed-lambda LP -- FEASIBLE"*. In a preprint this should
  be: *"feasible under HiGHS at floating-point precision, and
  separately verified exact-rational with 0 / 12,711,807
  constraint failures (Iteration 069a)"*.

- (Y) `iteration_077_diophantine_handoff_DESIGN.md` §1.1 input
  contract: *"each record is, by construction, a *legitimate*
  algebraic cycle candidate that has not yet been excluded"*. The
  word "legitimate" is loose; replace with *"is an algebraic
  cycle candidate that survives the Hercher and finite-
  verification layers as currently configured"*.

- (R) Any phrasing in commit messages or running commentary that
  reads *"Iteration 068 LP feasibility + 070 cycle-negativity
  ⇒ Collatz descent"*. Such an implication is **not** entailed
  by the cited iterations; 069b and 071B explicitly negate it.
  No such sentence should survive into the preprint.

- (Y) `changelog.md` 067 entry: *"this is a *universal* upper
  bound for ordinary-Collatz artefact cycles at K even"*. Hold
  the word "universal" only after stating the assumption that
  T = L·K is even; otherwise the bound shifts by the
  T-odd correction documented in iteration 067 itself.

- (R) Any phrasing of the form *"the LP framework as constructed
  cannot reach a Collatz proof"* read as a meta-mathematical
  certainty. Soften to *"the LP framework, in its present form,
  is not on a path to a full Collatz proof: the formula-drift
  vs actual-drift gap is incompatible with a state-level
  Lyapunov bound under any single λ"*. The negation is
  about *this approach*, not about *Collatz being unprovable*.

- (Y) `RESEARCH_AUDIT.md` Section B: claim that the notebook's
  `λ = log₂(3) − 1` is "novel". It is the maximum drift density
  per step under the no-adjacent-1s constraint and has been
  noted in the literature for compressed Collatz. Change
  *"possibly novel"* to *"the structural derivation … is, to
  our knowledge, written out cleanly here for the first time
  computationally; the constant itself is well-known"*.

## 8. Notation inconsistencies and citation mismatches

(Promoted to PASS 2.)

---

# PASS 2 — Theorem-and-citation consistency audit

## A. Notation inconsistencies

1. **`K` vs `T`.** Branch I uses `K` for the window length
   (concrete values 6, 8, 10). Branch II uses `T` for the period
   length (concrete values 12, 24, 36, 48). The relation
   `T = L·K` is stated in places but inconsistently. Fix: define
   both at first use in §2.2 and never re-define them in their
   "wrong" branch.

2. **`drift` definition.** Used as both *per-window*
   (`m_middle·(1 + log_2 3) − K`, Branch I) and *per-cycle*
   (`m·(1 + log_2 3) − T`, Branch II). The two are different
   objects. Fix: subscripts `drift_edge` vs `drift_cycle`, or
   rename the cycle-level quantity to `D_C`.

3. **`S` definition.** In Branch I: `S(e) = K − m_middle` is the
   per-edge even-step count. In Branch II: `S = T − m` is the
   total even-step count of the periodic cycle. They are summed
   per cycle in Branch I but defined directly in Branch II.
   Fix: same as `drift` — pick consistent subscripts.

4. **`m` ambiguity.** Sometimes "number of odd bits in
   `pi_middle`" (per-edge), sometimes "total odd-step count over
   `T` steps" (per-cycle). Same fix as `drift` and `S`.

5. **`ε` vs `eps` vs `epsilon`.** Three spellings appear in
   commit messages and JSON. The preprint should use `ε`
   uniformly; code blocks may keep `eps` / `epsilon`.

6. **`λ` value.** Both `0.584962500721157`,
   `LOG2_3_UPPER − 1 + 10⁻⁶`, and `LOG2_3_UPPER − 1 + ρ` appear.
   These agree numerically when `ρ = 10⁻⁶` but the `ρ` parameter
   should be defined exactly once (Branch I §3.3).

7. **`ψ`.** Sometimes `psi` (ASCII) in Markdown, sometimes `ψ`
   in math. Pick one for the preprint and be consistent.

8. **Classification labels.** Iteration 062 uses
   `non_realizable_*` (snake-case underscore), Iteration 072.5
   uses `NEGATIVE_OR_ZERO_DENOM` (UPPER_SNAKE), and Iteration
   064 uses both. Pick one (UPPER_SNAKE recommended for
   machine-readable schemas; snake-case for prose) and be
   consistent.

9. **Affine constants `A`, `B`, `denom`.**
   `A_str` / `A_dec` / `A_decimal` all appear in JSON outputs.
   Pick one (the NDJSON v2 schema settled on `A_str`); fix prose.

## B. Unsupported or weakly-supported claims

The following claims should be either backed up explicitly or
softened/removed.

- (Branch I, §3.6) "*the binding-edge subgraph is acyclic
  (a DAG skeleton)*". Supported by Iteration 071A's SCC
  computation (`0` non-trivial SCCs at K=6 and K=8). Strong;
  keep.
- (Branch I, §3.8) "*replacing formula drift by worst-case actual
  drift makes the LP infeasible*". Supported at K=6 (proven);
  for K=8 the LP solve was killed at 27 min CPU. Mark the K=8
  outcome as *"by analogous mechanism; LP solve aborted at 27
  min CPU; not strictly proven"* in the preprint. The K=6 proof
  is sufficient for the conceptual point.
- (Branch II, §4.4) "*Hercher m ≥ 92 bound is imported by
  reference*". Supported by inspection of the source (arXiv:2201.00406);
  good. The preprint should state explicitly: *"we do not re-
  derive this bound; we record provenance via
  `theorem_source = 'Hercher 2022 (arXiv:2201.00406)'` in every
  affected verdict"*.
- (Branch II, §4.7) The T ≤ 24 reproduction in Iteration 074
  was claimed but only the manifest is committed (no
  independent run record). Acceptable; the manifest is the
  artefact.
- (Iteration 067 / 068 derivations) "*λ = log_2 3 − 1 is forced
  by the no-adjacent-1s parity constraint*". The argument
  shown is correct *for even T*; for odd T the bound shifts
  by `O(1/T)` per Iteration 067's own derivation. The preprint
  must state the parity assumption explicitly when this λ is
  invoked.
- (RESEARCH_AUDIT closing) "*The notebook's framework cannot
  reach a Collatz proof in its current form*". This is a
  research-judgment claim, not a theorem. Phrase it as such.

## C. Citations needing wording sharpening

- **Hercher 2022 (arXiv:2201.00406)**. Title: *"There are no
  Collatz-m-Cycles with m ≤ 91"*. Cite as: *"Hercher (2022)
  proves that any non-trivial Collatz cycle has at least 92 odd
  elements"*. Avoid the formulation *"≥ 92 odd steps"* — the
  paper's `m` is the number of odd elements (also called rises)
  in the cycle. Operationally identical to "odd-step count" in
  the standard parity vector, but the wording should track the
  source.

- **Tao 2019 (arXiv:1909.03562)**. Title: *"Almost all orbits
  of the Collatz map attain almost bounded values"*. Cite as
  written; do **not** paraphrase as "almost all Collatz orbits
  reach 1" or as a partial proof. The result is logarithmic-
  density and uses a Syracuse iteration on a 3-adic skew random
  walk. Mention only in §5.2.

- **Eliahou (1993)**. *"The 3x+1 problem: new lower bounds on
  nontrivial cycle lengths"*, Discrete Math. 118. Cite for the
  continued-fraction lower bound on cycle length. Do not
  conflate with Hercher's `m`-bound.

- **Krasikov–Lagarias (2003)**. *"Bounds for the 3x+1 problem
  using difference inequalities"*, Acta Arith. 109. Cite as
  context, not as a primitive used by either branch.

- **Lagarias (1985)**. *"The 3x+1 problem and its
  generalizations"*, Amer. Math. Monthly 92. Cite as the
  foundational survey containing the parity-vector formulation.

- **Terras (1976)**. *"A stopping time problem on the positive
  integers"*, Acta Arith. 30. Cite for the parity-vector ↔
  residue-class bijection up to length K.

- **Roosendaal (ongoing)**. The verified bound `2⁶⁸` should be
  cited as a computational reference, not a theorem; phrase as
  *"at the time of writing, Roosendaal's verification covers
  positive integers up to ~2⁶⁸; we treat this as a trusted
  external bound"*.

## D. "proof" / "certificate" / "exclusion" / "verification" usage

These four words are doing distinct work in the existing materials
and must remain distinguished. The preprint should adopt:

- **proof**: reserved for established mathematical theorems
  imported from the cited literature (Hercher, Tao, etc.). The
  present work proves no Collatz-level theorem.

- **certificate**: a concrete data object (e.g. ψ; the
  `LinearFormVerdict` schema in 077) that, together with a
  verification procedure, attests to a property of a finite
  combinatorial structure.
  - **closed-graph cycle-negativity certificate** (Branch I): an
    exact-rational ψ such that every directed cycle in a closed
    finite graph has reweighted weight ≤ −|C|·ε.
  - **difference-potential certificate** (Branch I): synonym;
    use when emphasising that ψ is a state difference, not a
    Lyapunov function on values.
  - **Lyapunov descent certificate** (NOT achieved here): would
    be a state function `L: ℕ_{>0} → ℝ` strictly decreasing
    along positive-integer Collatz trajectories.
  - **(072.5) theorem verdict / theorem-backed exclusion**: a
    candidate-level verdict citing an imported theorem.

- **exclusion**: a mechanism that removes a candidate from
  further consideration. The CEE is an *exclusion engine*; it is
  not a *proof engine*.

- **verification**:
  - **exact rational verification** (Iteration 069a): re-checking
    a stored numerical artefact against `Fraction +
    LOG2_3_UPPER` arithmetic.
  - **finite verification** (072.5): the trusted external
    Roosendaal-class computation that `n ≤ 2⁶⁸` ⇒ Collatz reaches
    1 in finitely many steps.

The preprint must not blur these.

## E. Final claim-discipline assessment

| Aspect                                                   | Status |
|----------------------------------------------------------|:------:|
| No Collatz-conjecture proof claim                        | 🟢     |
| No silent extrapolation to actual integer dynamics       | 🟢     |
| Sharp separation of EXACT / CLOSED-SYM / SAMPLED / DIAG. | 🟢     |
| Negative-result preservation (069b, 071B, 075)           | 🟢     |
| Citation source attribution (Hercher, Tao, Eliahou…)     | 🟢     |
| Citation **wording precision** (Tao paraphrase, m-count) | 🟡     |
| Notation consistency (`K` vs `T`, `drift` overload)      | 🟡     |
| Status-label consistency (snake_case vs UPPER_SNAKE)     | 🟡     |
| LP/cycle-negativity vs Lyapunov language                 | 🟢     |
| `T ≤ 48` deferral framed as engineering, not math        | 🟢     |
| Iteration 077 framed as design, not implemented result   | 🟢     |
| Commit-message phrasings audited for stray claims        | 🟡     |

**Overall**: 🟢 **green** on claim discipline; 🟡 **yellow** on
mechanical consistency (notation, label casing, citation
wording). No red items if the §7 sentences are revised as
indicated.

---

# Recommended next editorial actions

1. Apply the §7 (overclaim) and §A (notation) fixes inline in
   `RESEARCH_AUDIT_2026-04-28.md`,
   `cycle_exclusion_engine/NOTE_periodic_word_engine.md`,
   `changelog.md`. No new content; only the wording deltas
   listed above.

2. Promote `EDITORIAL_REVIEW_2026-04-28.md` (this document) and
   `cycle_exclusion_engine/NOTE_periodic_word_engine.md` plus
   `RESEARCH_AUDIT_2026-04-28.md` together as the preprint
   package, in that order:
   1. NOTE (engineering branch, citable),
   2. RESEARCH_AUDIT (LP branch closure),
   3. EDITORIAL_REVIEW (this; meta-document; can be retained as
      an internal companion or stripped before submission).

3. Hold Iteration 077 design as a design document, not an
   appendix to the preprint. It belongs in a follow-up note.

4. After the §7 / §A revisions land, re-tag the repo as
   `preprint-ready-2026-04-28`.

No code is required for any of the above. No new mathematical
claim is introduced in this review.
