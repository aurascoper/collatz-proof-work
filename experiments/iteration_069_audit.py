"""Iteration 069: two-track audit of the Iteration 068 fixed-lambda LP.

069a -- exact rational LP verification.
  Re-enumerate the K-window graph; load the saved psi from
  certificates/iteration_068_certificate_K{K}.json; convert psi to
  exact Fraction; verify every edge constraint:

     psi[E2] - psi[E1] - lambda * S_edge <= -drift_edge - epsilon

  using
     lambda  = LOG2_3_UPPER - 1 + Fraction(rho_pad_num, 10**15)
     drift   = m * (1 + LOG2_3_UPPER) - K
     LOG2_3_UPPER = Fraction(1584962500721157, 10**15).

  Reports the number of constraints that fail in exact arithmetic and
  the max violation. If too many fail, recommend re-running 068 with
  a larger rho.

069b -- semantic fuel audit.
  For each (E1, E2) edge, compute the per-fiber `c_val := delta_2 -
  delta_1` from the canonical witness fiber (the n_example saved by
  the enumerator). Compare c_val to -S_edge.

  Question: is the credit -S_edge in the LP backed by an actual
  per-edge fuel drop in the integer trajectory, or only at the cycle
  level?

  Per-edge backing requires `c_val <= -S_edge`. If many edges have
  `c_val > -S_edge`, the credit is *not* a true per-edge Lyapunov; it
  is only consistent at the cycle level (where the per-edge c_val
  values telescope appropriately).

Outputs:
  proof_states/iteration_069a_exact_verify_K{K}.json
  proof_states/iteration_069b_fuel_audit_K{K}.json
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROOF_DIR = ROOT / "proof_states"
CERT_DIR = ROOT / "certificates"
PROOF_DIR.mkdir(parents=True, exist_ok=True)

K = int(os.environ.get("ITER_K", 8))
RHO_NUM = int(os.environ.get("ITER_RHO_NUM", 10**9))   # rho = RHO_NUM / 10**15
EPS_NUM = int(os.environ.get("ITER_EPS_NUM", 10**6))   # eps = EPS_NUM / 10**15
PSI_DENOM = int(os.environ.get("ITER_PSI_DENOM", 10**15))

LOG2_3_UPPER = Fraction(1584962500721157, 10**15)
LAMBDA_Q = LOG2_3_UPPER - 1 + Fraction(RHO_NUM, 10**15)
EPS_Q = Fraction(EPS_NUM, 10**15)


def simulate_window(n: int, k: int):
    m = 0; curr = n; mask = 0
    for _ in range(k):
        is_odd = curr & 1
        if is_odd:
            m += 1
            curr = 3 * curr + 1
        else:
            curr //= 2
        mask = (mask << 1) | int(is_odd)
    return m, curr, mask


def affine_constants(r: int, k: int):
    A, B, S = 1, 0, 0
    n = r
    for _ in range(k):
        b = n & 1
        if b == 1:
            B = 3 * B + (1 << S); A = 3 * A; n = 3 * n + 1
        else:
            S += 1; n //= 2
    return A, B, (1 << S) - A


DELTA_SAT = 64


def v2_int(val: int, cap: int = DELTA_SAT) -> int:
    if val == 0:
        return cap
    val = abs(val)
    raw = (val & -val).bit_length() - 1
    return raw if raw < cap else cap


def enumerate_edges(K: int):
    n_res = 1 << K
    n_fibers = 1 << (3 * K)
    aff = {}
    for r in range(n_res):
        A, B, denom = affine_constants(r, K)
        m, _, mask = simulate_window(r, K)
        aff[mask] = (B, denom, m)

    edges = {}  # key=(E1,E2), value=dict
    progress = max(1, n_fibers // 10)
    t0 = time.time()
    for n0 in range(1, n_fibers):
        n_sim = int(n0)
        m0, n1, pi_0 = simulate_window(n_sim, K)
        r1 = n1 & (n_res - 1)

        m1, n2, pi_1 = simulate_window(n1, K)
        r2 = n2 & (n_res - 1)
        B1, den1, _ = aff[pi_1]
        delta_1 = v2_int(n2 * den1 - B1)

        E1 = (r1, pi_0, r2, pi_1)

        m2, n3, pi_2 = simulate_window(n2, K)
        r3 = n3 & (n_res - 1)
        B2, den2, _ = aff[pi_2]
        delta_2 = v2_int(n3 * den2 - B2)

        E2 = (r2, pi_1, r3, pi_2)
        m_middle = m1
        S_middle = K - m_middle
        c_val = delta_2 - delta_1

        key = (E1, E2)
        if key not in edges:
            edges[key] = {
                "m_middle": m_middle, "S_middle": S_middle,
                "pi_middle": pi_1, "n_example": n_sim,
                "c_val_first_observed": c_val,
                "c_val_min": c_val,
                "c_val_max": c_val,
                "n_observations": 1,
            }
        else:
            info = edges[key]
            info["n_observations"] += 1
            if c_val < info["c_val_min"]:
                info["c_val_min"] = c_val
            if c_val > info["c_val_max"]:
                info["c_val_max"] = c_val
        if n0 % progress == 0:
            print(
                f"  enumerated {n0:>10}/{n_fibers}  edges={len(edges):,}  "
                f"elapsed={time.time()-t0:.1f}s",
                flush=True,
            )
    print(f"[069] enumeration: {len(edges):,} edges in {time.time()-t0:.1f}s")
    return edges


def load_psi(K: int) -> list:
    cert_path = CERT_DIR / f"iteration_068_certificate_K{K}.json"
    cert = json.loads(cert_path.read_text())
    return cert["psi"]


def main():
    t_overall = time.time()
    print(f"[069] K={K} lambda_global={LAMBDA_Q} (~{float(LAMBDA_Q):.15f})")
    print(f"[069]      epsilon={EPS_Q} (~{float(EPS_Q):.2e})")

    edges = enumerate_edges(K)
    psi_floats = load_psi(K)
    state_set = set()
    for (E1, E2) in edges:
        state_set.add(E1); state_set.add(E2)
    states = sorted(state_set)
    state_to_idx = {s: i for i, s in enumerate(states)}
    n_states = len(states)
    assert n_states == len(psi_floats), (n_states, len(psi_floats))

    # ---- 069a: exact rational verification
    print(f"[069a] converting {n_states:,} psi floats to Fraction ...")
    t0 = time.time()
    psi_q = [Fraction(p).limit_denominator(PSI_DENOM) for p in psi_floats]
    print(f"[069a] psi -> Fraction done in {time.time()-t0:.1f}s")

    print(f"[069a] verifying {len(edges):,} constraints exactly ...")
    n_fail = 0
    max_viol_q = Fraction(0)
    sample_failures = []
    one_plus_log2_3 = Fraction(1) + LOG2_3_UPPER
    t0 = time.time()
    progress_n = max(1, len(edges) // 10)
    for i, ((E1, E2), info) in enumerate(edges.items()):
        m = info["m_middle"]
        S_e = info["S_middle"]
        # drift_q = m * (1 + LOG2_3_UPPER) - K
        drift_q = Fraction(m) * one_plus_log2_3 - Fraction(K)
        i1 = state_to_idx[E1]; i2 = state_to_idx[E2]
        # required: psi[i2] - psi[i1] - lambda*S_e + drift_q + eps <= 0
        viol_q = (psi_q[i2] - psi_q[i1]) - LAMBDA_Q * Fraction(S_e) + drift_q + EPS_Q
        if viol_q > 0:
            n_fail += 1
            if viol_q > max_viol_q:
                max_viol_q = viol_q
            if len(sample_failures) < 20:
                sample_failures.append({
                    "E1": list(E1), "E2": list(E2),
                    "m": m, "S_edge": S_e,
                    "violation_str": str(viol_q),
                    "violation_float": float(viol_q),
                })
        if (i + 1) % progress_n == 0:
            print(
                f"  verified {i+1:>10}/{len(edges)}  fail={n_fail:,}  "
                f"max_viol={float(max_viol_q):.2e}  elapsed={time.time()-t0:.1f}s",
                flush=True,
            )
    t_verify = time.time() - t0
    proof_state_a = {
        "proof_state": "iteration_069a_exact_rational_verify",
        "K": K,
        "lambda_global_str": str(LAMBDA_Q),
        "epsilon_str": str(EPS_Q),
        "psi_denom_used": PSI_DENOM,
        "n_states": n_states,
        "n_edges": len(edges),
        "n_failed_constraints": n_fail,
        "fraction_failed": n_fail / len(edges) if edges else None,
        "max_violation_str": str(max_viol_q),
        "max_violation_float": float(max_viol_q),
        "verified_exact": n_fail == 0,
        "elapsed_seconds": t_verify,
        "interpretation": (
            "Exact rational re-verification of the iteration-068 LP "
            "certificate. If `verified_exact` is true, the K=" + str(K) +
            " fixed-lambda psi-only LP is feasible under exact "
            "Fraction + LOG2_3_UPPER arithmetic. If false, the LP "
            "boundary is too tight for the floating-point psi to "
            "survive rationalisation; re-run iteration 068 with larger "
            "rho or solve with higher precision."
        ),
        "sample_failures": sample_failures,
    }
    out_a = PROOF_DIR / f"iteration_069a_exact_verify_K{K}.json"
    out_a.write_text(json.dumps(proof_state_a, indent=2))
    print(f"[069a] wrote {out_a} (failed={n_fail}/{len(edges)}, "
          f"max_viol={float(max_viol_q):.2e})")

    # ---- 069b: semantic fuel audit
    print(f"[069b] auditing per-edge c_val vs -S_edge over {len(edges):,} edges ...")
    t0 = time.time()
    n_credit_backed = 0   # c_val_max <= -S_edge   (worst-case fiber satisfies)
    n_credit_min_backed = 0  # c_val_min <= -S_edge
    diff_hist = Counter()  # bucket on (c_val_first - (-S_edge))
    sample_unbacked = []
    for ((E1, E2), info) in edges.items():
        S_e = info["S_middle"]
        c_min = info["c_val_min"]
        c_max = info["c_val_max"]
        c_first = info["c_val_first_observed"]
        # Per-edge backed (worst-case fiber): c_max <= -S_e
        if c_max <= -S_e:
            n_credit_backed += 1
        else:
            if len(sample_unbacked) < 20:
                sample_unbacked.append({
                    "E1": list(E1), "E2": list(E2),
                    "S_edge": S_e,
                    "c_val_min": c_min, "c_val_max": c_max,
                    "c_val_first_observed": c_first,
                    "credit_minus_S_edge": -S_e,
                    "deficit": c_max - (-S_e),
                })
        if c_min <= -S_e:
            n_credit_min_backed += 1
        # Histogram of (c_first + S_e) (i.e. c_val - (-S_edge))
        diff = c_first + S_e
        bucket = diff
        if bucket > 8:
            bucket = 9
        elif bucket < -8:
            bucket = -9
        diff_hist[bucket] += 1
    t_audit = time.time() - t0

    proof_state_b = {
        "proof_state": "iteration_069b_semantic_fuel_audit",
        "K": K,
        "n_edges_audited": len(edges),
        "n_edges_credit_backed_worst_case": n_credit_backed,
        "fraction_credit_backed_worst_case": (
            n_credit_backed / len(edges) if edges else None
        ),
        "n_edges_credit_backed_some_fiber": n_credit_min_backed,
        "fraction_credit_backed_some_fiber": (
            n_credit_min_backed / len(edges) if edges else None
        ),
        "diff_histogram_c_val_plus_S_edge": dict(sorted(diff_hist.items())),
        "diff_buckets_legend": (
            "Each bucket b counts edges whose first-observed c_val = b - S_edge. "
            "Buckets >= 9 collapse 'much above' and <= -9 collapse 'much below'. "
            "b == 0 means c_val == -S_edge (credit exactly backed); "
            "b < 0 means c_val < -S_edge (credit over-backed); "
            "b > 0 means c_val > -S_edge (credit unbacked at this fiber)."
        ),
        "elapsed_seconds": t_audit,
        "sample_unbacked_edges": sample_unbacked,
        "fuel_drop_claim": "eta_after - eta_before <= -S_edge",
        "interpretation": (
            "Per-edge fuel audit. The LP credits each edge with -S_edge "
            "of fuel; this is BACKED (in worst-case fiber) iff "
            "c_val_max <= -S_edge. If a large fraction of edges fails "
            "this, the LP feasibility from 068 is *cycle-averaged* and "
            "NOT a true per-edge Lyapunov potential. The classifier 062 "
            "and the v_2-fuel lemma 066 still give a finite-shadow bound "
            "for any concrete trajectory; what is missing is a *state* "
            "function eta(E, n) whose per-edge drop equals -S_edge for "
            "every edge."
        ),
    }
    out_b = PROOF_DIR / f"iteration_069b_fuel_audit_K{K}.json"
    out_b.write_text(json.dumps(proof_state_b, indent=2))
    print(f"[069b] wrote {out_b} (credit-backed worst-case "
          f"{n_credit_backed}/{len(edges)} = "
          f"{100*n_credit_backed/len(edges):.1f}%)")

    print(f"[069] total elapsed {time.time()-t_overall:.1f}s")


if __name__ == "__main__":
    main()
