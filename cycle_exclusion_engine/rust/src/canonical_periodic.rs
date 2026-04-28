//! Canonical-rotation reducer for MSB-first periodic words.
//!
//! Returns the lexicographically smallest cyclic rotation. We use this
//! to deduplicate rotation classes during the periodic-word emission
//! step.

use crate::periodic::bit_at;

/// Rotate left by `shift`: word[i] -> word[(i + shift) mod t].
pub fn rotate_left_msb(word: u128, t: usize, shift: usize) -> u128 {
    let mut out = 0u128;
    for i in 0..t {
        let b = bit_at(word, t, (i + shift) % t);
        out = (out << 1) | (b as u128);
    }
    out
}

/// Render a length-`t` MSB-first word as a binary string.
pub fn to_bit_string(word: u128, t: usize) -> String {
    (0..t)
        .map(|i| if bit_at(word, t, i) == 1 { '1' } else { '0' })
        .collect()
}

/// Canonical rotation: lex-smallest u128 over all cyclic rotations.
/// Returns (canonical_word, shift_to_canonical).
pub fn canonical_rotation_msb(word: u128, t: usize) -> (u128, usize) {
    let mut best = word;
    let mut best_shift = 0usize;
    for s in 1..t {
        let r = rotate_left_msb(word, t, s);
        if r < best {
            best = r;
            best_shift = s;
        }
    }
    (best, best_shift)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn t4_canonical() {
        // 0b0011 rotations: 0011, 0110, 1100, 1001 -> min = 0011
        let (c, _) = canonical_rotation_msb(0b0011u128, 4);
        assert_eq!(c, 0b0011u128);
        let (c, _) = canonical_rotation_msb(0b1001u128, 4);
        assert_eq!(c, 0b0011u128);
    }

    #[test]
    fn idempotent() {
        for t in 2..=8 {
            for w in 0..(1u128 << t) {
                let (c, _) = canonical_rotation_msb(w, t);
                let (c2, _) = canonical_rotation_msb(c, t);
                assert_eq!(c, c2, "not idempotent for word {:b} t={}", w, t);
            }
        }
    }

    #[test]
    fn bit_string_round_trip() {
        // 0b1011 of length 4 -> "1011"
        assert_eq!(to_bit_string(0b1011u128, 4), "1011");
    }
}
