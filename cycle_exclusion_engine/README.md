# Cycle Exclusion Engine (CEE)

A two-language prototype for Collatz cycle exclusion via parity-block
enumeration, exact affine composition, and Diophantine classification.

**Phase 1 (Rust)** — high-throughput parity-block generator + affine
composer + canonical reducer.

**Phase 2 (Julia)** — exact fixed-point classifier + arbitrary-precision
verifier + Baker-bound interface (placeholder).

This is **not a Collatz proof** and is not intended to become one. It is
the recommended pivot from `RESEARCH_AUDIT_2026-04-28.md` Section E
(Path 4-prime): instead of upgrading the closed-graph LP to a Lyapunov
descent, we feed the notebook's parity enumeration into the existing
Diophantine cycle-exclusion framework (Hercher 2022 et al.).

---

## Architecture

```
                       ┌────────────────────┐
                       │ Parity Block       │  Phase 1, Rust
                       │ Generator          │  src/parity.rs
                       └─────────┬──────────┘
                                 │ admissible u64 masks (no adj. 1s)
                       ┌─────────▼──────────┐
                       │ Affine Block       │  Phase 1, Rust
                       │ Composer           │  src/affine.rs (BigInt)
                       └─────────┬──────────┘
                                 │ ParityBlock { mask_le, K, m, S, A, B, denom }
                       ┌─────────▼──────────┐
                       │ Canonical Reducer  │  Phase 1, Rust
                       │ (cycle rotations)  │  src/canonical.rs
                       └─────────┬──────────┘
                                 │ NDJSON  (shared/FORMAT.md)
                       ════════════════════════ Rust ↔ Julia boundary
                                 │
                       ┌─────────▼──────────┐
                       │ Fixed-Point        │  Phase 2, Julia
                       │ Classifier         │  src/CEEJulia.jl
                       └─────────┬──────────┘
                                 │ surviving (denom > 0, B/denom integer, n > 0)
                       ┌─────────▼──────────┐
                       │ Arbitrary-Precision│  Phase 2, Julia
                       │ Verifier (BigInt)  │
                       └─────────┬──────────┘
                                 │
                       ┌─────────▼──────────┐
                       │ Baker-Bound        │  Phase 2, Julia
                       │ Interface (stub)   │  see Hercher 2022
                       └────────────────────┘
```

## Build & test

```bash
# Phase 1 (Rust)
cd rust
cargo test --release    # 3 unit + 3 sanity tests pass
cargo build --release   # produces target/release/cee_generate

# Phase 2 (Julia)
cd ../julia
julia --project=. -e 'using Pkg; Pkg.add("JSON"); Pkg.precompile()'
julia --project=. test/runtests.jl
```

## Throughput report (Apple M-series, single-thread `--release`)

| K  | F_{K+2} (records) | Generation+composition (no I/O) | NDJSON write   | End-to-end (Rust+Julia) |
|----|-------------------:|----------------------------------|----------------|-------------------------|
| 12 | 377                | 1 ms (0.4 M rec/s)               | 1 ms           | < 1 s                   |
| 24 | 121,393            | 0.07 s (1.7 M rec/s)             | 0.2 s          | 2.7 s                   |
| 36 | 39,088,169 (F_38)  | 41 s (~1.0 M rec/s)              | n/a (bench)    | n/a                     |

K=36 single-threaded matches Iteration 057's full F_38 enumeration in 41
seconds. With `rayon` parallelisation (Phase 1.5, todo) we expect 10×
speedup on M4-class hardware. For K=44/48 the binary writer (todo) is
expected to outperform NDJSON by 5-10× on disk I/O.

## End-to-end pipeline result, K=24

```
121,393 parity blocks (F_26)

  NON_INTEGER_FIXED_POINT     118,009  (97.2 %)   — most cycles excluded structurally
  NEGATIVE_OR_ZERO_DENOM        3,380  ( 2.8 %)   — positivity-domain artefacts
  REALIZABLE_TRIVIAL                1            — n = 1 (the 1-2-4 cycle root)
  REALIZABLE_CANDIDATE              2            — rotations: n = 2 and n = 4
  NON_POSITIVE_FIXED_POINT          1
  ----------------------------------------------
  Total realisable               3            — exactly the trivial cycle's 3 elements
  Non-trivial Collatz cycles     0            — confirmed at K=24 windows
```

This is a re-derivation of a well-known result; the contribution of
this prototype is the *infrastructure* for scaling to higher K.

## Shared file format

See `shared/FORMAT.md`. NDJSON for human inspection and small batches; a
binary `bincode` path is sketched for batches > 10 M records.

## What's NOT in this prototype

- **No multi-window cycles**. The current pipeline enumerates single
  K-step parity blocks and tests them as length-1 cycles. Multi-window
  cycle enumeration (length-L cycles in the LP graph for L ≥ 2) would
  re-use the same affine composer via `ParityBlock::compose`.
- **No actual Baker bound**. `baker_lower_bound(m, S)` returns a coarse
  heuristic; replacing this with a verified bound (Laurent / Mignotte
  constants) is the main remaining work for a rigorous theorem.
- **No parallelisation of the Rust generator**. Single-threaded only;
  `rayon` integration is straightforward (chunk by mask prefixes) and
  is a 10x speed gain on M4.
- **No Hercher-style continued-fraction pre-filter**. Hercher (2022)
  uses CF approximations of `log 3 / log 2` to short-circuit cycle
  exclusion before Baker. This pipeline doesn't yet wire that in.

## Per program.md — no Collatz proof claimed

The pipeline currently re-derives well-known cycle-exclusion results
(no non-trivial cycle at K=24 windows). It is a *foundation* for
extending Hercher-class bounds with the notebook's parity enumeration,
not a Collatz proof in itself.

See:
- `RESEARCH_AUDIT_2026-04-28.md` Section E for the recommended
  Diophantine integration plan.
- `proof_states/iteration_069a_exact_verify_K8.json` for the LP-side
  achievement that this engine *replaces* (cleanly).
