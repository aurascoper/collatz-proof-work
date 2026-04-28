//! Canonical-form reduction for cyclic parity blocks.
//!
//! Given a cycle parity word as a list of K-bit window masks (or a
//! single concatenated mask of length K_total), all cyclic shifts
//! represent the same affine cycle. We canonicalise to the
//! lexicographically smallest rotation, treating the mask as a circular
//! bit string.
//!
//! For single-window cycles (length-1 cycles in the LP graph) this
//! simply means rotating the K-bit pattern.

/// Canonicalize a length-`k` cyclic bit string represented as a u64
/// (bit 0 = first step). Returns the lexicographically smallest
/// rotation (treating bit 0 as the least-significant cyclic position).
pub fn canonicalize_cycle(mask_le: u64, k: u32) -> u64 {
    if k == 0 {
        return 0;
    }
    let mask_k = if k >= 64 { u64::MAX } else { (1u64 << k) - 1 };
    let mut best = mask_le & mask_k;
    let mut cur = mask_le & mask_k;
    for _ in 1..k {
        // Rotate left by 1 within k bits
        let high = (cur >> (k - 1)) & 1;
        cur = ((cur << 1) | high) & mask_k;
        if cur < best {
            best = cur;
        }
    }
    best
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn k4_rotations() {
        // 0b0011 has rotations 0011, 0110, 1100, 1001 -> min = 0011
        assert_eq!(canonicalize_cycle(0b0011, 4), 0b0011);
        assert_eq!(canonicalize_cycle(0b0110, 4), 0b0011);
        assert_eq!(canonicalize_cycle(0b1100, 4), 0b0011);
        assert_eq!(canonicalize_cycle(0b1001, 4), 0b0011);
    }

    #[test]
    fn k1_trivial() {
        assert_eq!(canonicalize_cycle(0b0, 1), 0);
        assert_eq!(canonicalize_cycle(0b1, 1), 1);
    }

    #[test]
    fn idempotent() {
        for k in 1..=10u32 {
            for mask in 0..(1u64 << k) {
                let c = canonicalize_cycle(mask, k);
                assert_eq!(c, canonicalize_cycle(c, k));
            }
        }
    }
}
