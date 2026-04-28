# Cycle Exclusion Engine

A two-stage prototype for exact Collatz cycle-candidate exclusion.

## Purpose

This engine is **not** a proof of the Collatz conjecture. It is a front end for a Diophantine cycle-exclusion program.

It does four things:

1. generates **primitive cyclically admissible periodic parity words**,
2. composes their exact affine maps,
3. classifies fixed points exactly,
4. forwards only surviving candidates to theorem-based filters and analysis.

At the current milestone:
- the Rust generator is validated against known parity counts,
- the Julia classifier is exact,
- the trivial `1 -> 4 -> 2 -> 1` cycle is the only realized class seen in tested ranges,
- the Baker/Hercher layer is scaffolded and provenance-aware.

## Repository layout

The engine lives under
`~/Downloads/collatz-proof-work/cycle_exclusion_engine/`:

```text
cycle_exclusion_engine/
  rust/                          (Rust crate `cee_rust`)
    Cargo.toml
    src/
      lib.rs
      parity.rs                  (open-word generator, Iteration 072 base)
      periodic.rs                (cyclically-admissible periodic words)
      canonical.rs
      canonical_periodic.rs
      affine.rs
      affine_periodic.rs
      ndjson_periodic.rs
      record.rs
      writer.rs
      bin/
        cee_periodic_generate.rs (Iteration 072 CLI)
    src/main.rs                  (legacy `cee_generate` open-word CLI)
    tests/sanity.rs

  julia/                         (Julia package `CEEJulia`)
    Project.toml
    src/
      CEEJulia.jl
      periodic_reader.jl
      exact_classifier_periodic.jl
      baker_interface.jl
      candidate_export.jl
      pipeline_periodic.jl
      candidate_analyzer.jl
    test/runtests.jl
    scripts/
      run_072_5_and_072_6.jl

  scripts/
    run_cycle_engine.sh
    run_cycle_engine.py

  shared/FORMAT.md               (NDJSON record schema)
  Makefile                       (test / bench / cycle-engine targets)

  proof_states/                  (Iteration 072.5 / 072.6 outputs)
  candidates/                    (OPEN_CANDIDATE NDJSON / JSON)
  out/                           (Rust generator NDJSON output)
  logs/                          (per-stage stdout/stderr)
  manifests/                     (Python runner manifest JSON)
```

The earlier README references to `cee_rust/` and `CEEJulia/` are
preserved here as the canonical Cargo crate name and Julia module
name, even though the on-disk parent directory is `rust/` and `julia/`.

## Mathematical object

For a primitive cyclically admissible periodic parity word `w` of length `T`:
- `1` means odd step,
- `0` means even step,
- cyclic admissibility forbids adjacent `11` including wraparound.

Let:
- `m = number of 1s`,
- `S = T - m`.

The composed affine map is:

```math
T_w(n) = \frac{3^m n + B_w}{2^S}.
```

A periodic fixed point candidate must satisfy:

```math
(2^S - 3^m)n = B_w.
```

The engine uses this exact equation to classify:
- `NEGATIVE_OR_ZERO_DENOM`
- `NON_INTEGER_FIXED_POINT`
- `NON_POSITIVE_FIXED_POINT`
- `REALIZABLE_TRIVIAL`
- `REALIZABLE_CANDIDATE`
- `EXCLUDED_BY_FINITE_VERIFICATION`
- `EXCLUDED_BY_THEOREM`
- `OPEN_CANDIDATE`

## Phase split

### Rust: throughput

The Rust crate handles:
- primitive cyclically admissible word generation,
- canonical rotation reduction,
- exact affine composition using `BigInt`,
- NDJSON emission.

Why Rust:
- fast bit-level enumeration,
- easy parallel scaling later,
- exact integer support for composition.

### Julia: truth

The Julia package handles:
- NDJSON ingestion,
- exact fixed-point classification,
- theorem-backed exclusion interface,
- open-candidate export,
- high-precision candidate analysis.

Why Julia:
- natural `BigInt` workflow,
- easier exact arithmetic experimentation,
- convenient theorem/diagnostic layer.

## Quick start

All paths below are relative to
`~/Downloads/collatz-proof-work/cycle_exclusion_engine/`.

### 1. Rust generator (Iteration 072)

```bash
cd rust
cargo run --release --bin cee_periodic_generate -- \
  --t-min 1 --t-max 24 --primitive-only true \
  --output ../out/periodic_T24.ndjson
```

### 2. Julia theorem filter + analyzer (Iterations 072.5 + 072.6)

```bash
cd ../julia
CEE_PERIODIC_INPUT=../out/periodic_T24.ndjson \
  julia --project=. scripts/run_072_5_and_072_6.jl
```

### 3. End-to-end shell runner

```bash
./scripts/run_cycle_engine.sh
```

### 4. End-to-end manifest runner (recommended)

```bash
python3 scripts/run_cycle_engine.py
```

Both runners create `out/`, `logs/`, `proof_states/`, `candidates/`, and
`manifests/` automatically.

### Make targets

```bash
make test                # run Rust + Julia unit tests
make bench               # benchmark Rust generator at K=24, K=36
make cycle-engine        # run shell pipeline (T<=24 by default)
make cycle-engine-json   # run Python pipeline + manifest JSON
```

## Environment overrides

The top-level runners support:
- `T_MIN`
- `T_MAX`
- `RUN_TAG`
- `NDJSON_OUT`
- `PROOF_0725`
- `PROOF_0726`
- `OPEN_NDJSON`
- `OPEN_JSON`
- `ANALYZER_PRECISION_BITS`
- `ANALYZER_SHORTLIST_SIZE`

Example:

```bash
T_MAX=36 RUN_TAG=T36 ANALYZER_PRECISION_BITS=768 ANALYZER_SHORTLIST_SIZE=100 \
python3 scripts/run_cycle_engine.py
```

## Current theorem layer

The current Baker interface is a rigorous scaffold with explicit provenance.

Implemented modules:
1. **finite verification bound**
2. **odd-step lower bound** (Hercher-style interface)

The engine never silently excludes a candidate. Every exclusion is recorded with:
- theorem source,
- theorem version,
- exclusion reason,
- threshold data,
- notes.

## Output files

### Rust output

NDJSON rows look like (verified against actual output 2026-04-28):

```json
{
  "word_bits": "001",
  "T": 3,
  "m": 1,
  "S": 2,
  "A_str": "3",
  "B_str": "4",
  "denom_str": "1",
  "primitive": true,
  "cyclic_admissible": true,
  "canonical_rotation": "001",
  "rotation_index": 0
}
```

`T`, `S` are upper-case to match the canonical mathematical notation
(K-windows, S = total even steps); `m` is lower-case for symmetry with
`drift = m·log₂3 − S` in the Iteration 064 / 067 / 068 derivations.

### Julia 072.5 proof state

Contains:
- classification counts,
- enabled theorem modules,
- theorem config,
- per-word results,
- exported open candidates.

### Julia 072.6 proof state

Contains:
- high-precision `|m log 3 - S log 2|` diagnostics,
- continued-fraction proximity data,
- a ranked shortlist of the hardest surviving candidates.

## Expected behavior at current scale

For tested ranges like `T <= 24`, the expected result is:
- exactly one `REALIZABLE_TRIVIAL` class,
- zero nontrivial realizable cycles,
- zero open candidates.

This is **not** new Collatz progress by itself. It is a validation that the cycle-candidate engine is correct and ready for stronger Diophantine modules.

## Throughput reference

Observed prototype performance (Apple M-series, single-thread,
`cargo build --release`):

| Stage / range                        | Records          | Time   |
|---|---:|---:|
| Rust open-word K=36                  | 39,088,169 (F_38) |  41 s |
| Rust periodic T≤24 (primitive only)  | 12,216           | 0.25 s |
| Julia 072.5 + 072.6 on T≤24 NDJSON   | 12,216           | ~5 s  |
| Python manifest end-to-end (T≤24)    | 12,216           | ~7.5 s |

Run on 2026-04-28; reproduce with `make bench` and
`make cycle-engine-json`.

## What this engine is for

This engine is meant to support the **Diophantine pivot**:
- parity block generation,
- exact affine composition,
- candidate-cycle exclusion,
- eventual Baker/logarithmic-form integration.

It is **not** intended as a standalone Collatz proof engine.

## Honest scope

What it can currently do:
- exactly enumerate and classify candidate periodic blocks,
- export all surviving candidates with theorem provenance,
- rank hard candidates for further analysis.

What it cannot yet do:
- prove the Collatz conjecture,
- replace Baker-style linear-forms arguments,
- exclude all possible nontrivial cycles without stronger theorem modules.

## Recommended next steps

1. **072.5**: replace the Baker scaffold with explicit constants and theorem-backed exclusions.
2. **072.6**: rank surviving open candidates by logarithmic hardness.
3. **073**: scale to `T <= 36` and `T <= 48`.
4. **074**: integrate stronger explicit logarithmic-form bounds.

## One-line summary

The Cycle Exclusion Engine is a fast Rust + exact Julia front end for Collatz periodic-word exclusion, with explicit theorem provenance and a clean handoff to future Diophantine cycle-exclusion modules.
