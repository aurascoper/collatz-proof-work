//! Primitive cyclically-admissible periodic parity-word generator.
//!
//! For Iteration 072, a "periodic word" is a length-`T` binary string
//! intended to be read cyclically: bit 0 is step 0, bit T-1 is the last
//! step, and bit 0 follows bit T-1 in the loop.
//!
//! Cyclic admissibility (ordinary Collatz, no two adjacent odd steps):
//!     ∀ i in 0..T:  ¬(bit_at(i) == 1 ∧ bit_at((i+1) mod T) == 1).
//!
//! Primitivity:
//!     The word is not a repetition of any shorter divisor-length block.
//!
//! We pack words into u128 with bit `i` at the `(T-1-i)`-th position
//! (MSB = first step) so lex-min canonical rotation is the natural
//! u128 ordering. This matches the Iteration 072 spec.

/// Read bit `i` of a length-`T` word stored MSB-first.
#[inline]
pub fn bit_at(word: u128, t: usize, i: usize) -> u8 {
    debug_assert!(t > 0 && i < t && t <= 128);
    ((word >> (t - 1 - i)) & 1) as u8
}

#[inline]
pub fn popcount(word: u128) -> usize {
    word.count_ones() as usize
}

/// Cyclic admissibility for ordinary Collatz: no two adjacent odd bits
/// (including the wraparound from bit T-1 to bit 0).
pub fn is_cyclically_admissible(word: u128, t: usize) -> bool {
    if t == 0 {
        return false;
    }
    for i in 0..t {
        let a = bit_at(word, t, i);
        let b = bit_at(word, t, (i + 1) % t);
        if a == 1 && b == 1 {
            return false;
        }
    }
    true
}

pub fn divisors(n: usize) -> Vec<usize> {
    let mut out = Vec::new();
    for d in 1..=n {
        if n % d == 0 {
            out.push(d);
        }
    }
    out
}

/// A word is primitive iff it is not a repetition of any shorter
/// divisor-length block.
pub fn is_primitive(word: u128, t: usize) -> bool {
    for &d in &divisors(t) {
        if d == t {
            continue;
        }
        // Compare position i to position i mod d
        let mut is_repetition = true;
        for i in 0..t {
            if bit_at(word, t, i) != bit_at(word, t, i % d) {
                is_repetition = false;
                break;
            }
        }
        if is_repetition {
            return false;
        }
    }
    true
}

/// DFS enumerator for cyclically-admissible binary words of length `t`.
/// Excludes wraparound (last_bit, first_bit) == (1, 1).
///
/// Words are emitted MSB-first packed in u128.
pub fn enumerate_cyclically_admissible(t: usize) -> Vec<u128> {
    fn dfs(pos: usize, t: usize, first: u8, prev: u8, acc: u128, out: &mut Vec<u128>) {
        if pos == t {
            // Cyclic admissibility wraparound check
            if !(prev == 1 && first == 1) {
                out.push(acc);
            }
            return;
        }
        // Branch: next bit = 0
        dfs(pos + 1, t, if pos == 0 { 0 } else { first }, 0, acc << 1, out);
        // Branch: next bit = 1 (only if previous bit was 0)
        if prev == 0 {
            let new_first = if pos == 0 { 1 } else { first };
            dfs(pos + 1, t, new_first, 1, (acc << 1) | 1, out);
        }
    }
    let mut out = Vec::new();
    dfs(0, t, 0, 0, 0, &mut out);
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cyclic_admissibility_blocks_wraparound() {
        // Word "11" of length 2: bits 1, 1 -> wraparound 1-1 violates
        let word = 0b11u128;
        assert!(!is_cyclically_admissible(word, 2));
    }

    #[test]
    fn cyclic_admissibility_accepts_alternating() {
        // Word "10" of length 2: bits 1, 0 -> wraparound 0-1 OK
        let word = 0b10u128;
        assert!(is_cyclically_admissible(word, 2));
    }

    #[test]
    fn primitive_repeated_excluded() {
        // "1010" length 4 = repetition of "10" length 2 -> not primitive
        let word = 0b1010u128;
        assert!(!is_primitive(word, 4));
    }

    #[test]
    fn primitive_simple_kept() {
        // "1000" length 4 -> primitive
        let word = 0b1000u128;
        assert!(is_primitive(word, 4));
    }

    #[test]
    fn enumerate_T2_yields_3_words() {
        let words = enumerate_cyclically_admissible(2);
        // Length 2 cyclic-adm: 00, 01, 10. Excludes 11 (wraparound).
        assert_eq!(words.len(), 3);
        let s: std::collections::HashSet<_> = words.into_iter().collect();
        assert!(s.contains(&0b00));
        assert!(s.contains(&0b01));
        assert!(s.contains(&0b10));
    }

    #[test]
    fn enumerate_T3_excludes_111_and_wrap() {
        let words = enumerate_cyclically_admissible(3);
        // Length 3 cyclic-adm: 000, 001, 010, 100. Excludes 011 (wrap),
        // 110 (wrap), 101 (wrap), 111 (all).
        assert_eq!(words.len(), 4);
        for &w in &words {
            assert!(is_cyclically_admissible(w, 3), "word {:03b} marked admissible but isn't", w);
        }
    }
}
