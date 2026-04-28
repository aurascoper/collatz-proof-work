//! Exact affine composition for periodic (MSB-first) words.
//!
//! For a length-`t` periodic word `w` with bit `i` at the (t-1-i)-th
//! position, the canonical recurrence (time order, bit 0 first) is:
//! - `A := 1, B := 0, S := 0`
//! - for bit in time order:
//!   - if `bit == 1`:  `B = 3*B + 2^S`,  `A = 3*A`
//!   - else:           `S += 1`
//!
//! Returns `(A, B, m, S)` with `A = 3^m` and `S` = total even steps.

use num_bigint::BigInt;
use num_traits::{One, Zero};

use crate::periodic::bit_at;

pub fn compose_affine_periodic(word: u128, t: usize) -> (BigInt, BigInt, usize, usize) {
    let mut a = BigInt::one();
    let mut b = BigInt::zero();
    let mut m = 0usize;
    let mut s = 0usize;
    let mut pow2_s = BigInt::one();
    for i in 0..t {
        let bit = bit_at(word, t, i);
        if bit == 1 {
            b = &b * 3 + &pow2_s;
            a *= 3;
            m += 1;
        } else {
            s += 1;
            pow2_s <<= 1;
        }
    }
    (a, b, m, s)
}

pub fn denom_from(a: &BigInt, s: usize) -> BigInt {
    (BigInt::one() << s) - a
}

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;

    #[test]
    fn t3_word_100_gives_1_4_2_1_cycle() {
        // word = "100" MSB-first = bits [1,0,0] in time order
        // m=1, S=2, A=3, B=1, denom = 4 - 3 = 1, n = B/denom = 1.
        let word = 0b100u128;
        let (a, b, m, s) = compose_affine_periodic(word, 3);
        assert_eq!(a, BigInt::from(3));
        assert_eq!(b, BigInt::from(1));
        assert_eq!(m, 1);
        assert_eq!(s, 2);
        assert_eq!(denom_from(&a, s), BigInt::from(1));
    }

    #[test]
    fn t8_alternating_gives_negative_fixed_point() {
        // word = "10101010" MSB-first = bits [1,0,1,0,1,0,1,0] time order
        let word = 0b10101010u128;
        let (a, b, m, s) = compose_affine_periodic(word, 8);
        assert_eq!(a, BigInt::from(81));
        // For pi = "10101010" (first step odd) the canonical recurrence
        // gives B = 65; for pi = "01010101" (first step even) it gives
        // B = 130 / 2 = 65 -- but with the MSB-first encoding here the
        // 10101010 word starts odd, hence B = 65.
        assert_eq!(b, BigInt::from(65));
        assert_eq!(m, 4);
        assert_eq!(s, 4);
        // denom = 16 - 81 = -65; matches notebook 060c K=8 self-loop.
        assert_eq!(denom_from(&a, s), BigInt::from(-65));
    }
}
