# Shared file format — Rust ↔ Julia

The Rust generator/composer emits **parity-block records** that the Julia
classifier consumes. We use a simple newline-delimited JSON (NDJSON)
format for human inspection; an optional binary path is available for
high-throughput batches.

## NDJSON record (one parity-block per line)

```json
{
  "mask_le_hex": "0x55",   // mask in little-endian hex; bit i = parity at step i
  "K": 8,                  // total step count of this block
  "m": 4,                  // number of odd steps
  "S": 4,                  // number of even steps  (S = K - m)
  "A_dec": "81",           // 3^m, decimal string (BigInt-safe)
  "B_dec": "85",           // affine constant B, decimal string
  "denom_dec": "-65",      // 2^S - A, decimal string
  "is_self_loop_candidate": true,   // K = block length, single window
  "label": "K8L1_self"     // free-form tag, optional
}
```

Notes:
- `mask_le_hex` is little-endian: bit 0 of the integer = parity of step 0
  (the first step). This is the convention adopted by the Julia
  classifier and `cycle_classifier.py`. The Rust generator emits in this
  convention to avoid endian confusion.
- All large integers are emitted as decimal strings so `BigInt` parsing
  is one call away on the Julia side. Avoid scientific notation.
- The Julia classifier MUST verify `denom == (1 << S) - A` and
  `(B_dec, A_dec)` consistency on read.

## Optional binary format (`.bin`)

For batches > 10 M records the Rust binary writer can emit
`bincode`-encoded `ParityBlock` structs. The Julia side reads via
`PythonCall` or a hand-rolled little-endian reader; spec is:

```
[ u64 magic = 0x434545_50415254  (== "CEEPART")
  u64 record_count
  for i in 0..record_count:
    [ u32 K
    , u32 m
    , u64 mask_le
    , u32 A_byte_len, [u8; A_byte_len] A_be
    , u32 B_byte_len, [u8; B_byte_len] B_be
    ]
]
```

`*_be` are big-endian byte representations of the BigInts (`num-bigint::BigInt::to_signed_bytes_be`).

## Block-level constraints

The Rust generator only emits parity blocks satisfying the
ordinary-Collatz no-adjacent-odd-bits rule:

  for all i: NOT (mask_le[i] = 1 AND mask_le[i+1] = 1)

This matches `Iteration 057`'s F_38 enumeration.
