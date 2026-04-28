//! Admissible parity-block generator.
//!
//! Enumerates all `K`-bit masks (in little-endian) such that no two
//! adjacent bits are both 1 -- the ordinary-Collatz constraint.
//!
//! For `K = 36` this yields F_38 = 39 088 169 masks (matches notebook
//! Iteration 057).

/// Iterator over admissible parity masks of length `K`, packed as `u64`
/// (bit 0 = first step). Requires `K <= 62`.
pub struct AdmissibleParityIter {
    k: u32,
    /// Stack of (position, last_bit, mask_so_far) for DFS.
    stack: Vec<(u32, u8, u64)>,
}

impl AdmissibleParityIter {
    pub fn new(k: u32) -> Self {
        assert!(k <= 62, "u64-packed iterator supports K <= 62");
        let mut stack = Vec::with_capacity(2 * k as usize + 4);
        stack.push((0, 0, 0u64));
        Self { k, stack }
    }
}

impl Iterator for AdmissibleParityIter {
    type Item = u64;

    fn next(&mut self) -> Option<u64> {
        while let Some((pos, last_bit, mask)) = self.stack.pop() {
            if pos == self.k {
                return Some(mask);
            }
            // Push branch with next bit = 1 (only if last_bit == 0)
            if last_bit == 0 {
                self.stack.push((pos + 1, 1, mask | (1u64 << pos)));
            }
            // Push branch with next bit = 0
            self.stack.push((pos + 1, 0, mask));
        }
        None
    }
}

/// Convenience: count admissible parity masks of length `K` without
/// allocating them. Returns `F_{K+2}` (the standard Fibonacci result).
pub fn count_admissible(k: u32) -> u128 {
    if k == 0 {
        return 1;
    }
    let mut a: u128 = 1; // F_1
    let mut b: u128 = 1; // F_2
    for _ in 0..(k + 1) {
        let c = a + b;
        a = b;
        b = c;
    }
    a
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn count_matches_fibonacci() {
        // count_admissible(K) should equal F_{K+2}
        // F values: F_1 = 1, F_2 = 1, F_3 = 2, F_4 = 3, F_5 = 5, ..., F_38 = 39088169
        assert_eq!(count_admissible(0), 1);
        assert_eq!(count_admissible(1), 2);
        assert_eq!(count_admissible(2), 3);
        assert_eq!(count_admissible(3), 5);
        assert_eq!(count_admissible(36), 39088169);
    }

    #[test]
    fn enumerator_matches_count() {
        for k in 0..=10 {
            let iter_count = AdmissibleParityIter::new(k).count() as u128;
            assert_eq!(iter_count, count_admissible(k), "K={}", k);
        }
    }

    #[test]
    fn enumerator_emits_no_adjacent_ones() {
        for k in 1..=12 {
            for mask in AdmissibleParityIter::new(k) {
                let m = mask;
                let m_shifted = m >> 1;
                assert_eq!(m & m_shifted, 0,
                           "mask {:b} (K={}) has adjacent 1s", m, k);
            }
        }
    }

    #[test]
    fn k0_emits_empty_mask() {
        let v: Vec<u64> = AdmissibleParityIter::new(0).collect();
        assert_eq!(v, vec![0]);
    }
}
