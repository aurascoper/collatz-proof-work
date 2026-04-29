# Theorem-aware periodic-word exclusion engine for Collatz cycle candidates

> A reproducible pipeline that exhaustively enumerates primitive
> cyclically-admissible periodic parity words of bounded length,
> composes their exact affine maps over `BigInt`, classifies the
> algebraic fixed point under exact rational arithmetic, and
> dispatches surviving candidates through a theorem layer with
> machine-readable provenance. Demonstrated clean scaling through
> `T ≤ 36` (2,552,323 primitive words; 327 s end-to-end), with the
> only realisable class being the trivial `1–4–2` cycle. Not a
> Collatz proof; an auditable front end for Diophantine cycle-
> exclusion arguments.

**Branch**          Iterations 072 / 072.5 / 072.6 / 073 / 074 / 075
                    (partial) of `collatz-proof-work`.
**Status**          Frozen at commit `ae886f8` (2026-04-28). Citable.
**Strongest claim** For all primitive cyclically-admissible periodic
                    parity words of length `T ≤ 36`, the engine finds
                    exactly one realisable class (the trivial 1–4–2
                    cycle, canonical word "001", `n = 4`) and zero
                    non-trivial or open candidates.
**Out of scope**    Linear-forms-in-logarithms exclusion of any
                    `OPEN_CANDIDATE`s; Collatz divergence; orbits
                    that are not cycle candidates.

---

## 1. Definitions

### 1.1 Ordinary Collatz parity vector

For a positive integer `n`, the ordinary Collatz step is

  T(n) = (3n + 1) if n is odd,   T(n) = n / 2 if n is even.

The parity vector of `n` is the sequence `b_0 = n mod 2,
b_1 = T(n) mod 2, b_2 = T²(n) mod 2, …`.  After an odd step `n →
3n + 1`, the result is always even (since `3·odd + 1 = even`), so
**no two adjacent parity bits are both 1** in any ordinary-Collatz
parity vector. This is the no-adjacent-1s constraint used throughout
the pipeline.

### 1.2 Periodic parity word

A length-`T` binary word `w = (b_0, b_1, …, b_{T-1})` is *cyclically
admissible* iff no two adjacent bits in the cyclic order are both 1,
i.e. iff

  ∀ i ∈ {0, …, T-1}: ¬(b_i = 1 ∧ b_{(i+1) mod T} = 1).

A cyclically-admissible word `w` is *primitive* iff it is not a
repetition of any shorter divisor-length block.

### 1.3 Affine composition

For a parity word `w`, define A, B, S by the canonical recurrence:

  A := 1; B := 0; S := 0
  for b in w (time order):
      if b == 1:  B = 3B + 2^S;  A = 3A
      else:       S = S + 1

Let `m` denote the number of 1-bits, so `A = 3^m` and `S = T − m`.
The composed affine map on positive rationals is

  T_w(n) = (A·n + B) / 2^S.

A cycle candidate satisfies the fixed-point equation

  (2^S − 3^m)·n = B.

We write `denom := 2^S − 3^m`, the *cycle denominator*.

### 1.4 Classification

Following the engine's vocabulary (`exact_classifier_periodic.jl`):

| Label                          | Meaning                                                |
|--------------------------------|--------------------------------------------------------|
| `NEGATIVE_OR_ZERO_DENOM`       | `denom ≤ 0` (positivity-domain artefact, theorem 064)  |
| `NON_INTEGER_FIXED_POINT`      | `denom > 0` but `B mod denom ≠ 0`                      |
| `NON_POSITIVE_FIXED_POINT`     | `n_candidate = B / denom ≤ 0`                          |
| `REALIZABLE_TRIVIAL`           | `n ∈ {1, 2, 4}` and direct simulation traces back to `n` |
| `REALIZABLE_CANDIDATE`         | `n` integer > 4 and direct simulation closes (rare)    |
| `EXCLUDED_BY_FINITE_VERIFICATION` | `n ≤ N_0` (verified bound; defaults to 2^68)        |
| `EXCLUDED_BY_THEOREM`          | excluded by Hercher's `m ≥ 92` lower bound (default)   |
| `OPEN_CANDIDATE`               | survives all of the above; passes to deeper analysis   |

The dispatch order is structural → trivial → finite-verification →
odd-step theorem → open. Every theorem-based exclusion records its
source (e.g. `Hercher 2022 (arXiv:2201.00406)`), version, threshold,
numeric gap, and human-readable reason in the row's `baker_verdict`
sub-object.

---

## 2. Architecture

```
                       ┌────────────────────────────┐
                       │ Rust generator             │  Phase 1
                       │ cee_periodic_generate      │
                       │  - cyclic admissibility    │
                       │  - primitivity test        │
                       │  - canonical rotation      │
                       │  - exact BigInt affine     │
                       │  - NDJSON v2 output        │
                       └────────────┬───────────────┘
                                    │
                                    ▼
                       ┌────────────────────────────┐
                       │ Julia classifier (072)     │  Phase 2
                       │ classify_fixed_point_      │
                       │ periodic                   │
                       └────────────┬───────────────┘
                                    │
                                    ▼
                       ┌────────────────────────────┐
                       │ Theorem dispatcher (072.5) │
                       │ apply_baker_bound          │
                       │  - finite verification     │
                       │  - Hercher m ≥ 92 bound    │
                       │  - composite open path     │
                       └────────────┬───────────────┘
                                    │
                                    ▼
                       ┌────────────────────────────┐
                       │ Open-candidate export      │
                       │ + Candidate analyzer 072.6 │
                       │  - Δ = |m·log 3 − S·log 2| │
                       │  - CF convergents          │
                       │  - hardness ranking        │
                       └────────────────────────────┘
```

The Rust crate (`rust/`) is the throughput layer; the Julia package
(`julia/`) is the exactness layer. The boundary is a single NDJSON v2
schema documented in `shared/FORMAT.md`.

Three drivers wrap the chain: a Julia driver
(`julia/scripts/run_072_5_and_072_6.jl`), a shell driver
(`scripts/run_cycle_engine.sh`), and a Python driver with manifest
output (`scripts/run_cycle_engine.py`). The Python driver supports a
`CEE_PIPELINE_MODE` flag with values `072` (full chain) or `074`
(theorem-only).

---

## 3. Theorem layer

The current theorem layer is rigorous **by reference**: it does not
re-prove any theorem, but every exclusion records the source and
threshold so an external reviewer can verify which theorem was
applied to which candidate.

### 3.1 Finite verification bound

If `n_candidate ≤ N_0` for a trusted external Collatz verification
ceiling `N_0`, the candidate is excluded with verdict
`:excluded_by_verified_bound`. Default `N_0 = 2^68 ≈ 2.95·10^20`,
matching Roosendaal's published verification range.

### 3.2 Hercher odd-step lower bound

Hercher (2022, *There are no Collatz-m-Cycles with m ≤ 91*,
arXiv:2201.00406) proves that any non-trivial Collatz cycle has at
least 92 odd elements (equivalently, in the parity-vector sense, at
least 92 odd steps; we follow the source paper's "odd elements"
phrasing). The dispatcher applies this directly: any
non-trivial candidate with `m ≤ 91` is excluded with verdict
`:excluded_by_theorem` carrying

  theorem_source  = "Hercher 2022 (arXiv:2201.00406)"
  theorem_version = "odd-step lower bound for non-trivial Collatz cycles"
  required_min_m  = 92.

### 3.3 Open candidate

A candidate that survives both layers is labelled `OPEN_CANDIDATE`
and exported to NDJSON for downstream analysis. The 072.6 analyzer
ranks open candidates by ascending `Δ = |m·log 3 − S·log 2|`
(computed at 512-bit precision by default), pairs them with the
nearest continued-fraction convergent of `log_2 3`, and returns the
top-50 (configurable) shortlist.

In every scan executed to date (`T ≤ 36`), no candidate has reached
the `OPEN_CANDIDATE` bucket.

---

## 4. Results

### 4.1 T ≤ 12

| Bucket                          | Count |
|---------------------------------|------:|
| `NON_INTEGER_FIXED_POINT`       |    67 |
| `NEGATIVE_OR_ZERO_DENOM`        |    10 |
| `NON_POSITIVE_FIXED_POINT`      |     1 |
| `REALIZABLE_TRIVIAL`            |     1 |
| `REALIZABLE_CANDIDATE`          |     0 |
| `EXCLUDED_BY_FINITE_VERIFICATION` | 0   |
| `EXCLUDED_BY_THEOREM`           |     0 |
| `OPEN_CANDIDATE`                |     0 |
| **Total primitive words**       | **79** |

Runtime: < 1 s end-to-end.
The single realisable representative is the canonical word "001"
(time order: even, even, odd; n = 4) — the 1–2–4 cycle.

### 4.2 T ≤ 24

| Bucket                          | Count |
|---------------------------------|------:|
| `NON_INTEGER_FIXED_POINT`       | 11,757 |
| `NEGATIVE_OR_ZERO_DENOM`        |    457 |
| `NON_POSITIVE_FIXED_POINT`      |      1 |
| `REALIZABLE_TRIVIAL`            |      1 |
| `OPEN_CANDIDATE`                |      0 |
| **Total primitive words**       | **12,216** |

Runtime: ~7.5 s end-to-end (Rust 1.8 s + Julia 5.7 s).

### 4.3 T ≤ 36 (Iteration 073)

| Bucket                          | Count       |
|---------------------------------|------------:|
| `NON_INTEGER_FIXED_POINT`       | 2,513,649  (98.5 %) |
| `NEGATIVE_OR_ZERO_DENOM`        |    38,672  ( 1.5 %) |
| `NON_POSITIVE_FIXED_POINT`      |        1   |
| `REALIZABLE_TRIVIAL`            |        1   |
| `OPEN_CANDIDATE`                |        0   |
| **Total primitive words**       | **2,552,323** |

Runtime: 327 s end-to-end (Rust 196 s + Julia 106 s).
The theorem layer is correctly inactive at this scale: every
artefact is excluded structurally before it reaches the Hercher
dispatcher.

### 4.4 T ≤ 48 (Iteration 075, partial — engineering wall)

A T ≤ 48 attempt was launched on 2026-04-28 with the same pipeline.
The Rust generator ran for 34 min CPU and produced an NDJSON file of
**~6.4 GB** before the run was aborted because available disk fell
below 3 GB. The Julia stage was never reached.

Diagnostically: at T = 48, primitive cyclically-admissible periodic
words emit on the order of 100 M canonical NDJSON rows (per-row size
≈ 50 bytes once `A_str = 3^m` digits exceed the small-T regime). The
NDJSON v1 schema is not the right transport for this scale.

Implications for future scaling:

1. **Switch to a binary record format**. The schema sketched in
   `shared/FORMAT.md` (bincode-style with big-endian BigInt blobs)
   is expected to be roughly 3-5× more compact than NDJSON for
   T ≥ 40 and would also eliminate the JSON parsing overhead on the
   Julia side.
2. **Stream rather than buffer**. The current Julia reader loads
   the entire NDJSON corpus into a `Vector{PeriodicRecord}`. At
   T ≥ 40 we should switch to a streaming reader that classifies
   each record on-the-fly and accumulates only counts plus
   open-candidate exports.
3. **Shard by T**. Emitting one NDJSON per T (and one summary
   proof_state per shard) keeps any single file below ~1 GB through
   T = 44.

T ≤ 48 results are therefore **deferred** to a future Iteration 075
that implements at least one of the above. The current note's
strongest defensible claim remains the T ≤ 36 result.

### 4.5 Summary

> Within the scanned range, for every primitive cyclically-
> admissible periodic parity word of length T ≤ 36, the Cycle
> Exclusion Engine finds exactly one realisable class — namely
> the trivial 1–4–2 cycle (canonical word "001", n = 4) — and zero
> non-trivial realisable or open candidates. No claim is made
> about T > 36, nor about non-cyclic Collatz behaviour.

This is a re-derivation of a corollary of the existing literature
(Hercher 2022 excludes any non-trivial Collatz cycle with at most
91 odd elements, which is far more general than the periodic-word
exclusion at T ≤ 36 reproduced here). The contribution of this
engine is the auditable, reproducible infrastructure, not the
underlying mathematical fact.

---

### 4.6 Scaling table

| T (max) | Primitive words | Total runtime | Open candidates | Status   |
|--------:|----------------:|--------------:|----------------:|----------|
| 12      |              79 |        < 1 s  |               0 | clean    |
| 24      |          12,216 |         7.5 s |               0 | clean    |
| 36      |       2,552,323 |          327 s |               0 | clean    |
| 48      |         (~10⁸ projected) | aborted after 34 min CPU at NDJSON ~ 6.4 GB | n/a | **disk-limited; deferred** |

The clean-scaling regime is therefore T ≤ 36 with the current
NDJSON-based pipeline; pushing past T ≈ 40 requires a binary or
sharded format.

## 5. Scope and limitations

What the engine **does** establish:

1. Every primitive cyclically-admissible parity word of length
   T ≤ 36 is correctly enumerated and classified.
2. Each classification is backed either by exact integer arithmetic
   (structural verdicts) or by a referenced theorem (theorem layer).
3. The pipeline is reproducible from a single Python runner with a
   manifest JSON capturing every stage's return code, timing, and
   proof-state summary.

What the engine **does not** establish:

1. It does not prove the Collatz conjecture.
2. It does not re-prove Hercher's odd-step bound; that bound is
   imported by reference and explicitly recorded in every relevant
   verdict.
3. It does not exclude non-cyclic divergent orbits; the entire
   pipeline is about cycle candidates only.
4. It does not implement an explicit linear-forms-in-logarithms
   bound. The 072.6 analyzer can rank `OPEN_CANDIDATE`s by Δ but
   does not exclude them.

---

## 6. Reproducing the results

```bash
cd ~/Downloads/collatz-proof-work/cycle_exclusion_engine

# Tests
make test                              # 25 Rust + 20 Julia tests

# Scan T <= 24 (default mode 072: classifier + theorem + analyzer)
python3 scripts/run_cycle_engine.py

# Scan T <= 36 (fast on M-series; ~5-6 minutes)
T_MAX=36 RUN_TAG=T36 \
  ANALYZER_PRECISION_BITS=768 \
  ANALYZER_SHORTLIST_SIZE=100 \
  python3 scripts/run_cycle_engine.py

# Theorem-only mode
CEE_PIPELINE_MODE=074 python3 scripts/run_cycle_engine.py
```

Each invocation writes a manifest to `manifests/`, the per-stage
proof_state files to `proof_states/`, NDJSON outputs to `out/`,
candidate exports to `candidates/`, and per-stage logs to `logs/`.

The canonical proof_state files for Iterations 073 and 074 are
mirrored at the project root under
`../proof_states/iteration_073_periodic_cycle_engine_T36.json` and
`../proof_states/iteration_074_manifest_T24.json`.

---

## 7. References

- **Hercher 2022** "There are no Collatz-m-Cycles with m ≤ 91."
  arXiv:2201.00406. The cited odd-step lower bound used by the 072.5
  theorem layer.
- **Eliahou 1993** "The 3x+1 problem: new lower bounds on non-trivial
  cycle lengths." *Discrete Mathematics* 118, 45–56.
- **Krasikov–Lagarias 2003** "Bounds for the 3x+1 problem using
  difference inequalities." *Acta Arithmetica* 109, 237–258.
- **Tao 2019** "Almost all orbits of the Collatz map attain almost
  bounded values." arXiv:1909.03562. Logarithmic-density argument
  via 3-adic skew random walks; orthogonal to cycle exclusion but
  provides context for the broader landscape.
- **Lagarias 1985** "The 3x+1 problem and its generalizations."
  *American Mathematical Monthly* 92, 3–23. Foundational survey.
- **Roosendaal**, ongoing computational verification of Collatz on
  positive integers up to ~2^68. Used as the trusted finite
  verification bound `N_0` in the engine's theorem layer.

---

## 8. Honest closure

The Cycle Exclusion Engine branch (Iterations 072, 072.5, 072.6,
073, 074) achieves what a candidate-cycle front-end should achieve:

  - exact enumeration over a well-defined mathematical object,
  - exact classification with no silent exclusions,
  - explicit theorem provenance for every theorem-based verdict,
  - reproducible runners with machine-readable manifests,
  - tests covering the boundary cases.

It is solid infrastructure. It is not, and is not advertised as, a
Collatz proof. The next research target — for anyone wishing to
extend this engine — is not more enumeration but the integration of
an explicit linear-forms-in-logarithms module that consumes the
`OPEN_CANDIDATE` exports and excludes them rigorously rather than by
reference.

The engine is now ready for that handoff.
