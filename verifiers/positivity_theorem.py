"""Positivity-domain theorem for ordinary-Collatz periodic affine cycles.

Formal statement
----------------

Let `b_1, ..., b_T` be a sequence of parity bits with `m` odd bits and
`S = T - m` even bits, and let `A := 3^m`. Compose the time-ordered
recurrence

    A0 = 1, B0 = 0, S0 = 0
    for bit b_i:
        if b_i == 1:
            B = 3*B + 2^S;  A = 3*A
        else:
            S += 1

Let `B`, `S` be the final values after T steps. The composed affine map
is `T_pi(n) = (A n + B) / 2^S`, and the affine fixed point is

    n_pi := B / (2^S - A) = B / (2^S - 3^m).

Define the (per-cycle) drift
    Drift := m * (1 + log_2 3) - T.

THEOREM ("positivity-domain theorem"). For any T-step periodic affine
cycle of the ordinary-Collatz map (m >= 1):

    Drift > 0   <==>   3^m > 2^S   <==>   2^S - 3^m < 0.

In particular, every strictly positive-drift periodic affine cycle has

    n_pi = B / (2^S - 3^m) <= 0,

i.e. its affine fixed point is non-positive. **Such a cycle therefore
cannot exist in the positive integers** -- it is at best a 2-adic /
negative-integer / Q-rational artefact of the affine extension.

Proof sketch
------------

Drift > 0
  iff  m * (1 + log_2 3) > T = m + S
  iff  m * log_2 3 > S
  iff  log_2 (3^m) > S
  iff  3^m > 2^S.

Hence `2^S - 3^m < 0`, i.e. denom < 0.

Recurrence shows that for m >= 1 we have B > 0 (every odd step injects
`+ 2^S_at_step >= 1` into B, and subsequent multiplications by 3 keep
it positive). With B > 0 and denom < 0,

    n_pi = B / denom < 0.

If `B % denom != 0` then no integer fixed point exists at all.
Either way, `n_pi` is not a positive integer. QED.

Computational verification
--------------------------

`assert_positivity_theorem(pi_middles, K)` returns a dict with the exact
A, B, S, denom, drift sign and whether the theorem statement holds for
the given periodic parity word. The function is symbolic / exact
(integer arithmetic only); the only floating-point step is rendering
the "drift_sign" label.
"""

from __future__ import annotations

from typing import Iterable


def _bits_time_order_from_pi(pi_middle: int, K: int) -> list[int]:
    return [(pi_middle >> j) & 1 for j in range(K - 1, -1, -1)]


def assert_positivity_theorem(pi_middles: Iterable[int], K: int) -> dict:
    """Verify the positivity-domain theorem for one periodic parity word.

    Returns a dict including:
      - exact A, B, S, m_total, T_total
      - denom = 2^S - 3^m (exact integer)
      - drift_sign: "+", "-", or "0", computed via the exact integer
        comparison `3^m vs 2^S`
      - non_positive_fixed_point: True if no positive-integer cycle
        exists (denom <= 0, or denom > 0 but B/denom is not a positive
        integer)
      - theorem_consistent: True iff drift_sign == "+" implies denom < 0
        (the theorem)
    """
    bits = []
    for pi in pi_middles:
        bits.extend(_bits_time_order_from_pi(int(pi), K))

    A, B, S = 1, 0, 0
    m_total = 0
    for b in bits:
        if b == 1:
            B = 3 * B + (1 << S)
            A = 3 * A
            m_total += 1
        else:
            S += 1
    T = len(bits)
    pow2S = 1 << S

    # Exact drift sign via integer comparison: drift > 0 iff A = 3^m > 2^S.
    if A > pow2S:
        drift_sign = "+"
    elif A < pow2S:
        drift_sign = "-"
    else:
        drift_sign = "0"

    denom = pow2S - A

    # Theorem: drift_sign == "+" iff denom < 0.
    theorem_consistent = (
        (drift_sign == "+" and denom < 0)
        or (drift_sign == "-" and denom > 0)
        or (drift_sign == "0" and denom == 0)
    )

    if denom <= 0:
        non_positive_fixed_point = True
        candidate_n = None
    else:
        if B % denom != 0:
            non_positive_fixed_point = True
            candidate_n = None
        else:
            n = B // denom
            candidate_n = n
            non_positive_fixed_point = n <= 0

    return {
        "T_total_steps": T,
        "m_odd_steps": m_total,
        "S_even_steps": S,
        "A_3_to_m": A,
        "B_value": B,
        "pow2_S": pow2S,
        "denom_2S_minus_3m": denom,
        "drift_sign": drift_sign,
        "candidate_n_pi": candidate_n,
        "non_positive_fixed_point": non_positive_fixed_point,
        "theorem_consistent": theorem_consistent,
    }


def positivity_theorem_statement() -> str:
    return (
        "THEOREM: For any T-step periodic ordinary-Collatz parity word "
        "with m >= 1 odd bits and S = T - m even bits, let A = 3^m and "
        "B as defined by the canonical recurrence. Then the affine "
        "fixed point n_pi = B / (2^S - A) is NOT a positive integer "
        "whenever the cycle has strictly positive total drift "
        "Drift = m * (1 + log_2 3) - T > 0; equivalently whenever "
        "3^m > 2^S. PROOF: Drift > 0 iff 3^m > 2^S iff 2^S - 3^m < 0; "
        "for m >= 1 we have B > 0; therefore n_pi = B / (2^S - 3^m) "
        "<= 0. QED."
    )
