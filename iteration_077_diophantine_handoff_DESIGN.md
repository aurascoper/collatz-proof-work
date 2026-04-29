# Iteration 077 — Diophantine handoff layer (DESIGN ONLY)

**Status**     DRAFT, design only, no code.
**Date**       2026-04-28.
**Posture**    Engineering branch (CEE) frozen at `ae886f8`. This
               document opens a new mathematical branch and does not
               modify CEE code.
**Prereq**     CEE pipeline through Iteration 074 (`OPEN_CANDIDATE`
               export schema is stable). Not blocked on Iteration 076
               (binary transport).

The CEE branch produces a clean stream of cycle candidates with
machine-readable theorem provenance. Iteration 077 is the first
iteration that consumes that stream as input rather than producing
graph or LP outputs, and is therefore a separable mathematical
module.

The goal is **not** to upgrade the CEE; it is to begin building the
explicit linear-forms-in-logarithms exclusion layer that the CEE was
always intended to feed.

---

## 1. Inputs and outputs

### 1.1 Input contract

A length-bounded NDJSON stream of `OPEN_CANDIDATE` records emitted by
`cycle_exclusion_engine/julia/src/candidate_export.jl`:

```json
{
  "word_bits": "...",
  "canonical_rotation": "...",
  "T": <int>,
  "m": <int>,
  "S": <int>,
  "n_candidate_str": "<decimal BigInt>",
  "baker_verdict": { ... 072.5 verdict ... },
  "notes": "..."
}
```

For every record the CEE has already verified:
- `denom = 2^S − 3^m > 0`
- `B mod denom == 0`
- `n_candidate = B / denom > 0`
- direct simulation closes the cycle from `n_candidate`
- `n_candidate > N_0` (otherwise it would have been
  `EXCLUDED_BY_FINITE_VERIFICATION`)
- `m ≥ 92` (otherwise it would have been `EXCLUDED_BY_THEOREM` under
  Hercher 2022)

So each record is, by construction, a *legitimate* algebraic cycle
candidate that has not yet been excluded by any theorem currently in
the dispatcher.

### 1.2 Output contract

For every input record, Iteration 077 emits exactly one of:

| Verdict                         | Meaning                                                                |
|---------------------------------|------------------------------------------------------------------------|
| `EXCLUDED_BY_LINEAR_FORM`       | `|m·log 3 − S·log 2|` is below an explicit Baker-class lower bound that contradicts the cycle constraint. |
| `OPEN_DIOPHANTINE`              | the linear-forms layer cannot yet exclude this candidate; passes downstream. |
| `INPUT_INCONSISTENCY`           | the record fails one of the input-contract checks; refuse to process.  |

Output rows preserve full provenance (theorem source, version, used
constants, numeric gap, candidate identifier).

---

## 2. Mathematical scaffold

### 2.1 The cycle linear form

For a candidate cycle of length `T` with `m` odd steps and `S = T − m`
even steps, the algebraic cycle constraint
`(2^S − 3^m) n_candidate = B` forces

  Λ_C := |m · log 3 − S · log 2|

to be small in a precise sense relative to `n_candidate`. Concretely
(Lagarias 1985; Hercher 2022):

  Λ_C · n_candidate · (2^S − 3^m) ≤ const · max(B, 1)

so any explicit lower bound on `Λ_C` becomes an upper bound on the
*size* of admissible cycles, and conversely any admissible cycle of
length `T` requires `Λ_C` to be exponentially small in `T`.

### 2.2 Baker-class lower bounds

Two reference results are used as theorem primitives:

1. **Laurent–Mignotte–Voutier (1991/2000)**
   For non-zero `Λ = b₁ log α₁ − b₂ log α₂` with `α_i ∈ Q* ∩ R_{>0}`:
     |Λ| ≥ exp(−C(α₁, α₂) · log B · log B')
   with explicit constants `C, B = max(|b_i|), B' = ...`.
2. **Hercher 2022 (arXiv:2201.00406)**
   Combines (1) with the Collatz cycle equation to derive
   `m ≥ 92` for any non-trivial cycle. (Already encoded by reference
   in 072.5; not re-implemented here.)

The 077 module's job is to expose result (1) at the API level — not
to re-derive it. The verifier consumes published constants and emits
a machine-checkable verdict.

---

## 3. API surface (sketch only; no implementation)

### 3.1 Julia module name

`CEEDiophantine` (in a new `cycle_exclusion_engine/julia_077/` package
or as an extension submodule of `CEEJulia`).

### 3.2 Types

```julia
struct LinearFormInput
    word_bits::String
    T::Int
    m::Int
    S::Int
    n_candidate::BigInt
    A::BigInt        # = 3^m
    B::BigInt
    denom::BigInt    # = 2^S - A
end

struct LinearFormConstants
    source::String           # e.g. "Laurent-Mignotte-Voutier 2000"
    version::String          # specific corollary used
    C::BigFloat              # the explicit constant from the theorem
    B0::BigFloat             # auxiliary constant if any
    notes::String
end

struct LinearFormVerdict
    status::Symbol           # :excluded_by_linear_form / :open_diophantine
                             # / :input_inconsistency
    Lambda_lower_bound::BigFloat       # provable lower bound on Λ_C
    Lambda_required_upper_bound::BigFloat  # cycle equation forces this
    contradiction_witness::String      # human-readable
    constants_used::LinearFormConstants
end
```

### 3.3 Functions

```julia
verify_input_contract(input::LinearFormInput)::Bool
compute_required_Lambda_upper(input)::BigFloat
compute_Baker_Lambda_lower(input, consts)::BigFloat
apply_linear_form_exclusion(input; consts)::LinearFormVerdict
```

### 3.4 Driver

`scripts/run_077.jl`: reads OPEN_CANDIDATE NDJSON from CEE, applies
`apply_linear_form_exclusion` per record, writes
`proof_states/iteration_077_linear_form_exclusion_<tag>.json` with:

```json
{
  "proof_state": "iteration_077_linear_form_exclusion",
  "n_input_records": ...,
  "counts": {
    "EXCLUDED_BY_LINEAR_FORM": ...,
    "OPEN_DIOPHANTINE": ...,
    "INPUT_INCONSISTENCY": ...
  },
  "constants_source": "Laurent-Mignotte-Voutier 2000",
  "open_diophantine_export": "candidates/iteration_077_open_diophantine_<tag>.ndjson"
}
```

---

## 4. Acceptance criteria

Iteration 077 is *complete* when:

1. The Julia module compiles and tests pass.
2. The constants block (`LinearFormConstants`) is populated from a
   single explicitly cited published result; the citation appears in
   every verdict's provenance.
3. Running 077 on the empty CEE OPEN_CANDIDATE stream produces an
   empty proof_state (no spurious verdicts).
4. Running 077 on a synthetic adversarial fixture (a fabricated
   candidate with `m ≥ 92`, `n_candidate > 2^68`, plausible Λ_C)
   produces either `:excluded_by_linear_form` or `:open_diophantine`
   with a complete provenance record.
5. No verdict is silently produced; `:input_inconsistency` is the
   only allowed early-exit.

Iteration 077 does **not** require:
- Producing a new mathematical theorem.
- Any non-trivial Collatz statement.
- Re-running the CEE.

---

## 5. Risks and non-goals

1. **Re-deriving Baker constants is out of scope.** This module
   imports them from the literature, with citation, and refuses to
   guess.
2. **No silent fallback.** If the constants cannot be applied to a
   record (e.g. the input violates the contract), the verdict is
   `:input_inconsistency` and the candidate is *not* excluded.
3. **Performance is irrelevant in 077.** OPEN_CANDIDATE volume is
   currently zero through `T ≤ 36`; the module's first job is
   correctness, not throughput.
4. **No Collatz proof.** Even a fully-functional 077 only excludes
   *cycle* candidates, not divergent orbits. Tao 2019's logarithmic-
   density result remains the strongest "almost all orbits" bound;
   077 has no claim on that direction.

---

## 6. Sequencing

```
Iteration 077  (this design)        — Diophantine API + literal Baker
                                       constant import.
Iteration 078  (future)             — exhaustive verification of the
                                       imported constants against an
                                       independent reference.
Iteration 079  (future)             — sensitivity sweep: at what `T`
                                       does the imported bound start
                                       to lose discrimination power?
Iteration 080+ (future, optional)   — explicit re-derivation of a
                                       weaker but self-contained
                                       Baker-class bound, if the
                                       imported reference proves
                                       insufficient.
```

Iteration 076 (CEE binary transport) remains dormant until any
iteration in the 077-079 chain demands an OPEN_CANDIDATE volume that
NDJSON cannot deliver.

---

## 7. Honest closure

This document is a design, not a result. It establishes the API
surface for a Diophantine handoff layer that will consume the CEE
output and produce a single, theorem-cited verdict per candidate. No
mathematical claim is made beyond what 072.5 already records by
reference. The current `OPEN_CANDIDATE` count from the CEE through
T ≤ 36 is zero; the 077 module is therefore not yet on the critical
path for any active claim, and its value is preparatory.

**The mathematically live branch from this point is 077, not 076.**
The engineering branch (CEE) is checkpointed and citable as written.
