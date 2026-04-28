//! Cycle Exclusion Engine -- Phase 1 (Rust)
//!
//! Generates admissible parity blocks (no adjacent odd bits) under the
//! ordinary-Collatz constraint, composes their affine maps exactly via
//! `num-bigint::BigInt`, and emits records compatible with the Julia
//! Phase-2 classifier.
//!
//! # Conventions
//!
//! - `mask_le`: a u64 in little-endian -- bit `i` is the parity of step
//!   `i` of the parity block. Bit 0 = first step. (Differs from
//!   `iteration_*.py` MSB-first encoding; consumers must convert.)
//! - `m`: number of odd steps = `mask_le.count_ones() as u32`.
//! - `S`: number of even steps = `K - m`.
//! - `A`: `3^m` as `BigInt`.
//! - `B`: affine offset accumulated by the canonical recurrence.
//! - `denom`: `2^S - A` as `BigInt`.
//!
//! # Affine recurrence (canonical)
//!
//! Following the user-specified ordering: bits in *time order* (bit 0
//! first), and the recurrence
//!
//! ```text
//!     A := 1, B := 0, S := 0
//!     for bit in time order:
//!         if bit == 1:
//!             B = 3 * B + 2^S
//!             A = 3 * A
//!         else:
//!             S += 1
//! ```
//!
//! After `K` steps the composed map is `T(n) = (A * n + B) / 2^S`.
//!
//! # Throughput notes
//!
//! - Generation is enumeration over Fibonacci-counted strings; we use
//!   the standard "all binary strings without 11" iterator.
//! - Affine composition reuses `BigInt` allocations where possible.
//! - For `K <= 62` we keep masks in `u64`; for `K > 62` we use
//!   `Vec<bool>` (slower path).

pub mod parity;
pub mod affine;
pub mod canonical;
pub mod record;
pub mod writer;

pub use parity::AdmissibleParityIter;
pub use affine::ParityBlock;
pub use canonical::canonicalize_cycle;
pub use record::ParityBlockRecord;
pub use writer::{NdjsonWriter, BinaryWriter};
