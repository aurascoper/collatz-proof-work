"""Cycle admissibility classifier (Iteration 062).

Given an ordered list of `pi_middle` parity masks (each of length K bits)
representing a candidate Collatz cycle in our edge-state encoding, this
module composes the affine map and tests whether any positive integer
realises the cycle.

Pipeline:
  1. Concatenate pi_middle bits in time order. Each pi is stored with the
     first time-step at the highest bit position (matches `mask = (mask
     << 1) | bit` in the enumerators).
  2. Compose the affine map via the canonical recurrence:
         A=1, B=0, S=0
         for bit in time order:
             if bit == 1:
                 B = 3*B + (1<<S);  A = 3*A
             else:
                 S += 1
  3. Solve (2^S - A) * n = B exactly.
  4. Realisability requires: denom = 2^S - A > 0, B % denom == 0,
     n = B // denom > 0.
  5. Verify by arbitrary-precision direct simulation: starting at n,
     run len(bits) Collatz steps; the observed parity sequence must
     equal the concatenated bits, and the final value must equal n.

Classification labels:
  - "REALIZABLE_POSITIVE_INTEGER_CYCLE"
  - "non_realizable_negative_or_zero_denom"
  - "non_realizable_non_integer_fixed_point"
  - "non_realizable_non_positive_n"
  - "non_realizable_simulation_parity_mismatch"
  - "non_realizable_simulation_did_not_return_to_n"
"""

from __future__ import annotations

from typing import Iterable


def _bits_time_order_from_pi(pi_middle: int, K: int) -> list[int]:
    """Convert a K-bit pi_middle integer to a list of bits in time order.

    The encoder packs bit 0 (first step) at the high end via
    `mask = (mask << 1) | bit`, so we read MSB first.
    """
    return [(pi_middle >> j) & 1 for j in range(K - 1, -1, -1)]


def classify_cycle(pi_middles: Iterable[int], K: int) -> dict:
    """Classify a candidate cycle described by a sequence of pi_middle masks.

    `pi_middles` is iterable of K-bit ints (one per cycle edge), in cycle
    order. Returns a dict with the classification, including the candidate
    integer n (when defined), the affine constants A, B, S, and the
    diagnostic that distinguishes the failure mode.
    """
    bits = []
    pi_list = list(pi_middles)
    for pi in pi_list:
        bits.extend(_bits_time_order_from_pi(int(pi), K))

    A, B, S = 1, 0, 0
    for b in bits:
        if b == 1:
            B = 3 * B + (1 << S)
            A = 3 * A
        else:
            S += 1

    denom = (1 << S) - A
    n_total_steps = len(bits)
    n_odd_steps = sum(bits)

    base = {
        "K": K,
        "n_edges": len(pi_list),
        "n_total_steps": n_total_steps,
        "n_odd_steps": n_odd_steps,
        "A_3_to_m": A,        # = 3^m
        "B_value": B,
        "S_total_divisions": S,
        "denom_2S_minus_A": denom,
        "denom_positive": denom > 0,
    }

    if denom <= 0:
        base["classification"] = "non_realizable_negative_or_zero_denom"
        base["explanation"] = (
            "2^S - 3^m is non-positive: the cycle has at least as many odd "
            "steps as the divisor balance allows; no positive integer fixed "
            "point. (3-bias too large.)"
        )
        return base

    if B % denom != 0:
        base["classification"] = "non_realizable_non_integer_fixed_point"
        base["B_mod_denom"] = B % denom
        return base

    n = B // denom
    base["candidate_n"] = n

    if n <= 0:
        base["classification"] = "non_realizable_non_positive_n"
        return base

    # Arbitrary-precision direct simulation from n.
    sim_n = n
    sim_bits = []
    for _ in range(n_total_steps):
        b = sim_n & 1
        sim_bits.append(b)
        if b == 1:
            sim_n = 3 * sim_n + 1
        else:
            sim_n //= 2

    if sim_bits != bits:
        # Find the first divergence index for diagnostics.
        idx = next(
            (i for i, (a, b_) in enumerate(zip(sim_bits, bits)) if a != b_),
            min(len(sim_bits), len(bits)),
        )
        base["classification"] = "non_realizable_simulation_parity_mismatch"
        base["first_divergence_index"] = idx
        base["expected_bits_around"] = bits[max(0, idx - 4):idx + 4]
        base["simulated_bits_around"] = sim_bits[max(0, idx - 4):idx + 4]
        return base

    if sim_n != n:
        base["classification"] = "non_realizable_simulation_did_not_return_to_n"
        base["sim_final_n"] = sim_n
        return base

    base["classification"] = "REALIZABLE_POSITIVE_INTEGER_CYCLE"
    base["realisable"] = True
    return base


def classify_cycle_from_bits_string(bin_strs: Iterable[str], K: int) -> dict:
    """Convenience: same as `classify_cycle` but takes K-bit binary strings."""
    return classify_cycle([int(s, 2) for s in bin_strs], K)
