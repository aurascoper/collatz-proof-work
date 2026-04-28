//! End-to-end sanity tests: enumerate at K=8, compose, verify against
//! direct Collatz simulation for n that match the parity.

use cee_rust::{AdmissibleParityIter, ParityBlock};
use num_bigint::BigInt;
use num_traits::Zero;

/// Find SOME positive integer n whose K-step parity equals `mask_le`.
/// Brute-force: try n = 1..2^(K+8); panic if none found.
fn find_realizing_n(mask_le: u64, k: u32) -> Option<u64> {
    for n in 1..=(1u64 << (k + 8)) {
        let mut cur = n;
        let mut ok = true;
        for i in 0..k {
            let expected = (mask_le >> i) & 1;
            let actual = cur & 1;
            if actual != expected {
                ok = false;
                break;
            }
            if expected == 1 {
                cur = 3 * cur + 1;
            } else {
                cur >>= 1;
            }
        }
        if ok {
            return Some(n);
        }
    }
    None
}

#[test]
fn affine_matches_direct_simulation_K8() {
    let k = 8;
    let mut tested = 0;
    for mask_le in AdmissibleParityIter::new(k) {
        let pb = ParityBlock::from_mask(mask_le, k);
        // Find an n whose first K parities match mask_le
        let n = match find_realizing_n(mask_le, k) {
            Some(n) => n,
            None => continue,
        };
        // Direct simulation
        let mut cur = n;
        for _ in 0..k {
            if cur & 1 == 1 {
                cur = 3 * cur + 1;
            } else {
                cur >>= 1;
            }
        }
        let direct = BigInt::from(cur);

        // Formula: (A * n + B) / 2^S
        let pow2_s = BigInt::from(1) << pb.s;
        let num = &pb.a * BigInt::from(n) + &pb.b;
        assert_eq!(&num % &pow2_s, BigInt::zero(),
                   "formula must produce integer: mask={:08b} n={}", mask_le, n);
        let formula = num / pow2_s;
        assert_eq!(formula, direct,
                   "formula != direct simulation: mask={:08b} n={}", mask_le, n);
        tested += 1;
    }
    assert!(tested > 0, "must have tested at least one mask");
    eprintln!("verified {} K=8 masks against direct simulation", tested);
}

#[test]
fn k8_known_self_loop_artefact() {
    // Iteration 060c K=8 self-loop has pi=10101010 in MSB-first encoding;
    // in our LE encoding bit-0-first that's mask_le = 0b01010101 = 0x55
    // (first step odd, then alternating).
    let pb = ParityBlock::from_mask(0x55u64, 8);
    assert_eq!(pb.m, 4);
    assert_eq!(pb.s, 4);
    assert_eq!(pb.a, BigInt::from(81));
    assert_eq!(pb.b, BigInt::from(65));
    assert_eq!(pb.denom, BigInt::from(-65));
    // Fixed point: B/denom = 65 / -65 = -1 (matches 060c witness)
}

#[test]
fn count_at_k36_matches_F38() {
    // F_38 = 39_088_169; matches Iteration 057.
    assert_eq!(cee_rust::parity::count_admissible(36), 39_088_169);
}
