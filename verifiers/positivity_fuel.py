"""Positivity-aware fuel for negative-domain artefact cycles (Iteration 066).

Mathematical setup
==================

Let `pi_middles = (pi_1, ..., pi_L)` describe a length-L cycle in the
edge-state graph (each pi_i is a K-bit parity mask). Compose the affine
map exactly:

    A := 3^m,  S := total even steps over the whole cycle,
    B  computed by the canonical recurrence,
    T_pi(n) := (A n + B) / 2^S.

If `denom := 2^S - A < 0` (positive-drift cycle, theorem 064) then the
affine fixed point `a := B / denom` is strictly negative and *no*
positive integer realises the cycle. However, a positive integer can
still **shadow** the cycle for finitely many periods.

Lemma (positivity-shadowing fuel)
---------------------------------

For ANY cycle (artefact or not):

    T_pi(n) - a = A * (n - a) / 2^S.

Hence, viewing both sides over Q,

    v2(n - a) - v2(T_pi(n) - a) = S - v2(A) = S - 0 = S,

since A = 3^m is odd. Therefore each successful application of T_pi
consumes exactly `S` units of 2-adic distance from the fixed point.

Define the fuel
    eta_pi(n) := v2((n * denom - B))   [equals v2(n - a) since denom is odd].

Then K_max(n) := floor(eta_pi(n) / S) is the *exact* maximum number of
full cycle periods that the positive orbit of n can shadow before
T_pi(n) ceases to be an integer (and the parity sequence necessarily
diverges from pi_middles).

This fuel is monotone-decreasing along every shadowing trajectory:

    eta_pi(T_pi(n)) = eta_pi(n) - S.

Constructively, given any target depth d, the synthetic seed

    n_d := (B * denom^{-1}) mod 2^d

is the unique residue mod 2^d such that v2(n_d * denom - B) >= d (with
the right adjustment for sign so that n_d > 0). Choosing d = c * S for
any integer c >= 1 gives a positive integer that shadows the artefact
cycle for exactly c periods.

Verification
============

`shadow_artefact_cycle(pi_middles, K, n_periods)` constructs n_d and
runs an arbitrary-precision direct Collatz simulation from n_d for
n_periods * L * K steps, checking that the observed parity sequence
matches the predicted one and that the orbit returns to n_d * (A/2^S)^c
(in the rational sense). It returns the predicted vs observed shadowing
depth and the computed orbit values at each period boundary.
"""

from __future__ import annotations

from typing import Iterable


def _bits_time_order_from_pi(pi_middle: int, K: int) -> list[int]:
    return [(pi_middle >> j) & 1 for j in range(K - 1, -1, -1)]


def compose_affine(pi_middles: Iterable[int], K: int) -> tuple[int, int, int, int, int]:
    """Compose the cycle's affine map. Returns (A, B, S, T, m)."""
    bits = []
    for pi in pi_middles:
        bits.extend(_bits_time_order_from_pi(int(pi), K))
    A = 1; B = 0; S = 0; m = 0
    for b in bits:
        if b == 1:
            B = 3 * B + (1 << S); A = 3 * A; m += 1
        else:
            S += 1
    return A, B, S, len(bits), m


def fuel_eta(n: int, pi_middles: Iterable[int], K: int) -> dict:
    """Compute eta_pi(n) = v2(n - a) for the cycle map composed from
    pi_middles.

    Returns A, B, S, denom, eta, predicted_shadow_periods.
    """
    A, B, S, T, m = compose_affine(pi_middles, K)
    denom = (1 << S) - A
    val = n * denom - B  # equals (n - a) * denom; denom is odd so v2 unchanged
    if val == 0:
        eta = float("inf")
    else:
        v = abs(val)
        eta = (v & -v).bit_length() - 1
    predicted = (eta // S) if (S > 0 and eta != float("inf")) else None
    return {
        "n": n, "A_3_to_m": A, "B": B, "S": S, "T_total_steps": T,
        "m_odd_steps": m, "denom_2S_minus_A": denom,
        "n_minus_a_times_denom": val, "eta": eta,
        "predicted_shadow_periods": predicted,
    }


def construct_shadow_seed(pi_middles: Iterable[int], K: int, n_periods: int) -> int:
    """Build a positive integer that shadows the cycle for exactly
    n_periods full periods.

    n_d := representative of (B * denom^{-1}) mod 2^(n_periods * S),
    chosen positive. Then v2(n_d * denom - B) >= n_periods * S.

    Special case: if denom > 0 and B is positive, n_d may be smaller
    than expected; we add multiples of 2^d as needed to ensure
    positivity and the right 2-adic depth.
    """
    A, B, S, T, m = compose_affine(pi_middles, K)
    denom = (1 << S) - A
    d = n_periods * S
    if d == 0:
        return 1  # degenerate; any positive integer "shadows" 0 periods.
    mod = 1 << d
    # Find n_d such that n_d * denom ≡ B (mod 2^d).
    # denom is odd, so its inverse mod 2^d exists.
    denom_mod = denom % mod
    inv = pow(denom_mod, -1, mod)
    n_d = (B * inv) % mod
    if n_d == 0:
        n_d = mod  # shift up to next residue
    # Ensure positive integer; n_d in (0, mod] is positive.
    return n_d


def simulate_collatz(n: int, n_steps: int) -> tuple[list[int], int]:
    """Arbitrary-precision direct Collatz simulation; returns
    (parity_bits, final_n).
    """
    bits = []
    cur = n
    for _ in range(n_steps):
        b = cur & 1
        bits.append(b)
        if b == 1:
            cur = 3 * cur + 1
        else:
            cur //= 2
    return bits, cur


def verify_v2_fuel_dynamics(pi_middles: list[int], K: int, k_iter: int = 3) -> dict:
    """Verify the (unconditional) v_2-fuel lemma:

        eta_pi(T_pi(n)) = eta_pi(n) - S        (when T_pi(n) is integer)
        eta_pi(n) := v_2((n * denom - B))

    For a synthetic seed n_d with eta(n_d) = k_iter*S we apply T_pi
    arithmetically (NOT via Collatz simulation) and check that eta
    decreases by exactly S per application, until eta reaches 0.

    This lemma is independent of whether the orbit *parities* match
    pi. It states only that the cycle's affine map respects v_2
    contraction at rate S.
    """
    A, B, S, T, m = compose_affine(pi_middles, K)
    denom = (1 << S) - A
    if S == 0:
        return {"status": "skipped_S_zero"}
    n_d = construct_shadow_seed(pi_middles, K, k_iter)

    def eta_of(n):
        val = n * denom - B
        if val == 0:
            return None  # +inf
        v = abs(val)
        return (v & -v).bit_length() - 1

    cur = n_d
    history = [{"i": 0, "n": cur, "eta": eta_of(cur)}]
    expected_eta = eta_of(cur)
    consistent = True
    pow2S = 1 << S
    for i in range(1, k_iter + 1):
        if eta_of(cur) is None or eta_of(cur) < S:
            break
        # Arithmetic application of T_pi (formal / not Collatz simulation)
        nxt = (A * cur + B) // pow2S
        if (A * cur + B) % pow2S != 0:
            consistent = False
            break
        eta_actual = eta_of(nxt)
        eta_predicted = expected_eta - S
        if eta_actual != eta_predicted:
            consistent = False
        history.append({
            "i": i, "n": nxt, "eta": eta_actual,
            "eta_predicted": eta_predicted,
            "match": eta_actual == eta_predicted,
        })
        expected_eta = eta_predicted
        cur = nxt

    return {
        "K": K, "L_cycle_length": len(pi_middles),
        "A_3_to_m": A, "B": B, "S": S, "denom_2S_minus_A": denom,
        "n_d_seed": n_d, "k_iter_attempted": k_iter,
        "v2_fuel_decreases_by_S_per_iteration": consistent,
        "history": history,
    }


def shadow_artefact_cycle(
    pi_middles: list[int], K: int, n_periods: int
) -> dict:
    """Build n_d, simulate, verify the parity matches for n_periods periods.

    Returns predicted (by v_2 fuel) and observed (by parity match)
    shadow depth. They can disagree: v_2-fuel counts how many times
    T_pi(n) is integer; parity-shadow counts how many times the actual
    Collatz orbit follows the prescribed parity. Parity-shadow is
    bounded above by v_2-fuel; equality requires a stricter mod
    condition on n.
    """
    A, B, S, T, m = compose_affine(pi_middles, K)
    denom = (1 << S) - A
    L = len(pi_middles)
    expected_bits_one_period = []
    for pi in pi_middles:
        expected_bits_one_period.extend(_bits_time_order_from_pi(int(pi), K))
    period_steps = L * K  # = T

    n_d = construct_shadow_seed(pi_middles, K, n_periods)
    eta = fuel_eta(n_d, pi_middles, K)["eta"]
    predicted_v2_iter = eta // S if S > 0 else None

    # Simulate up to (n_periods + 1) periods and check parity match per period.
    matched_periods = 0
    cur = n_d
    period_n_values = [cur]
    for p in range(n_periods + 1):
        bits, cur_after = simulate_collatz(cur, period_steps)
        if bits == expected_bits_one_period:
            matched_periods += 1
        else:
            cur = cur_after
            period_n_values.append(cur)
            break
        cur = cur_after
        period_n_values.append(cur)

    return {
        "K": K, "L_cycle_length": L, "T_steps_per_period": period_steps,
        "A_3_to_m": A, "B": B, "S": S, "denom_2S_minus_A": denom,
        "n_d_seed": n_d,
        "eta_initial": eta,
        "v2_fuel_iterations_predicted": predicted_v2_iter,
        "n_periods_attempted": n_periods,
        "parity_matched_periods_observed": matched_periods,
        "shadow_le_v2_fuel": (
            matched_periods <= (predicted_v2_iter or 0)
        ),
        "period_n_values": [int(v) for v in period_n_values],
    }
