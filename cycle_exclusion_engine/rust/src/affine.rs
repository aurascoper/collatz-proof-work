//! Exact affine composition for parity blocks.
//!
//! Given a parity block `mask_le` of length `K`, computes:
//! - `A = 3^m`,
//! - `B = canonical recurrence sum`,
//! - `S = K - m`,
//! - `denom = 2^S - A`.
//!
//! All arithmetic is exact via `num-bigint::BigInt`.

use num_bigint::BigInt;
use num_traits::{One, Zero};

#[derive(Debug, Clone)]
pub struct ParityBlock {
    pub mask_le: u64,
    pub k: u32,
    pub m: u32,
    pub s: u32,
    pub a: BigInt,
    pub b: BigInt,
    pub denom: BigInt,
}

impl ParityBlock {
    /// Compose the affine map for the given little-endian mask of
    /// length `K`. Bits are read in *time order*: bit 0 is step 0
    /// (first step). Matches `iteration_*.py` semantics after the
    /// MSB↔LSB conversion documented in `shared/FORMAT.md`.
    pub fn from_mask(mask_le: u64, k: u32) -> Self {
        let mut a = BigInt::one();
        let mut b = BigInt::zero();
        let mut s: u32 = 0;
        // pow2_s tracks 2^s alongside the recurrence
        let mut pow2_s = BigInt::one();
        let mut m: u32 = 0;
        for i in 0..k {
            let bit = (mask_le >> i) & 1;
            if bit == 1 {
                // B = 3*B + 2^S; A = 3*A
                b = &b * 3 + &pow2_s;
                a *= 3;
                m += 1;
            } else {
                s += 1;
                pow2_s <<= 1; // 2^(s)
            }
        }
        // denom = 2^S - A (where 2^S is pow2_s after final shift)
        let denom = &pow2_s - &a;
        Self { mask_le, k, m, s, a, b, denom }
    }

    /// Compose blocks: chaining two parity blocks of lengths K1 and K2
    /// into a single parity block of length K1 + K2.
    /// (Useful for extending a block to higher K without re-walking.)
    pub fn compose(&self, other: &ParityBlock) -> ParityBlock {
        // T_other ∘ T_self  for orbits processed in time order:
        // self first (bits 0..k1), then other (bits k1..k1+k2).
        // Result mask: self.mask_le | (other.mask_le << k1)
        let mask = self.mask_le | (other.mask_le << self.k);
        let k = self.k + other.k;
        // Composition: (A_other * A_self) n + (A_other * B_self * 2^{S_other}) ... actually
        // Let T_self(n) = (A_s n + B_s) / 2^{S_s}.
        // Let T_other(x) = (A_o x + B_o) / 2^{S_o}.
        // T_other(T_self(n)) = (A_o (A_s n + B_s)/2^{S_s} + B_o) / 2^{S_o}
        //                   = (A_o A_s n + A_o B_s + B_o 2^{S_s}) / 2^{S_s + S_o}.
        // So new A = A_o A_s, new B = A_o B_s + B_o 2^{S_s}, new S = S_s + S_o, new m = m_s + m_o.
        let pow2_ss = BigInt::from(1) << self.s;
        let new_a = &other.a * &self.a;
        let new_b = &other.a * &self.b + &other.b * &pow2_ss;
        let new_s = self.s + other.s;
        let pow2_new_s = BigInt::from(1) << new_s;
        let new_denom = &pow2_new_s - &new_a;
        ParityBlock {
            mask_le: mask, k, m: self.m + other.m, s: new_s,
            a: new_a, b: new_b, denom: new_denom,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;

    /// Direct Collatz simulation to verify affine composition.
    fn simulate(n: BigInt, mask_le: u64, k: u32) -> BigInt {
        let mut cur = n;
        for i in 0..k {
            let bit = (mask_le >> i) & 1;
            // Verify: actual parity of cur must match expected bit
            let cur_bit: u8 = if (&cur % 2u32) == BigInt::from(0) { 0 } else { 1 };
            assert_eq!(cur_bit, bit as u8, "parity mismatch at step {}", i);
            if bit == 1 {
                cur = cur * 3 + 1;
            } else {
                cur >>= 1;
            }
        }
        cur
    }

    #[test]
    fn affine_matches_simulation_k_small() {
        // Iterate over a few admissible masks; for each, find an integer n
        // whose K-step parity matches mask, simulate, and compare with formula.
        let k = 4;
        for mask_le in 0..(1u64 << k) {
            // skip if any adjacent bits both = 1
            if (mask_le & (mask_le >> 1)) != 0 { continue; }
            let pb = ParityBlock::from_mask(mask_le, k);
            // For mask_le, find SOME n that produces this parity.
            // Simplest: try every n up to 2^k (parity of K steps from n is
            // determined by lower bits in a known but non-trivial way).
            for n_lo in 1..(1u64 << k) {
                let n_big = BigInt::from(n_lo);
                // Try to simulate; skip if parity mismatches
                let result = std::panic::catch_unwind(|| simulate(n_big.clone(), mask_le, k));
                if let Ok(n_after) = result {
                    // formula: (A n + B) / 2^S
                    let pow2_s = BigInt::from(1) << pb.s;
                    let num = &pb.a * &n_big + &pb.b;
                    assert_eq!(&num % &pow2_s, BigInt::from(0),
                               "expected 2^S | (A n + B), mask={:b}", mask_le);
                    let formula = num / pow2_s;
                    assert_eq!(formula, n_after,
                               "formula != simulation, mask={:b} n={}", mask_le, n_lo);
                }
            }
        }
    }

    #[test]
    fn k8_alternating_self_loop_negative_fixed_point() {
        // pi = 0xAA = 10101010 in MSB-first; in little-endian bit-0-first
        // that's 0x55 = 01010101 (alternating starting with 0).
        // But we want the alternating starting with 1 in time order:
        // mask_le bit 0 = 1, bit 1 = 0, bit 2 = 1, ...
        let mask_le = 0b01010101u64; // bits 0,2,4,6 are 1
        let k = 8;
        let pb = ParityBlock::from_mask(mask_le, k);
        assert_eq!(pb.m, 4);
        assert_eq!(pb.s, 4);
        assert_eq!(pb.a, BigInt::from(81));
        // denom = 16 - 81 = -65
        assert_eq!(pb.denom, BigInt::from(-65));
        // For the alternating mask starting with odd, B should be 65
        // (matches notebook Iteration 064, where the depth-free K=8
        // self-loop has fixed point n = -1 = B/denom = 65/-65).
        assert_eq!(pb.b, BigInt::from(65));
    }
}
