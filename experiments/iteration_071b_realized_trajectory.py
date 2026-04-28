"""Iteration 071B: realized-trajectory restriction.

The 068 LP uses the *formula* drift

    drift_formula(e) = m_middle * (1 + log_2 3) - K
                     = m * log_2 3 - S       (algebraic identity)

as the per-edge cost. This is the asymptotic / large-n limit of the
actual log_2 change along the integer orbit.

For a real positive integer n traversing window pi (composed affine
map T_pi(n) = (3^m * n + B_pi) / 2^S), the *actual* per-window drift is

    drift_actual(n) = log_2(T_pi(n) / n)
                    = m * log_2 3 + log_2(1 + B_pi / (3^m * n)) - S
                    = drift_formula + log_2(1 + B_pi / (3^m * n))

Hence drift_actual(n) >= drift_formula always (B_pi > 0 for m >= 1),
and the LP using formula drift is *optimistic*: a realised-trajectory
LP is strictly tighter.

This iteration computes, for every edge e in the closed K-graph and
every fiber n0 in our enumeration that realises e, the actual drift
drift_actual(n_pi) where n_pi is the value entering the executed
pi_middle window. We then check whether 068's psi certificate
satisfies the *realised-trajectory* LP:

    psi(E_2) - psi(E_1) <= lambda * S(e) - drift_actual_max(e) - eps

for every edge e, where drift_actual_max(e) is the worst-case
realised drift over all fibers traversing e.

If yes: the 068 psi survives the realised-trajectory restriction --
strong evidence that the certificate corresponds to actual integer
descent and not just an aggregated abstraction.

If no: report the violating edges and their excess drift; this is
the residual gap between the formula LP and the realised-trajectory
LP.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

ROOT = Path(__file__).resolve().parent.parent
PROOF_DIR = ROOT / "proof_states"
CERT_DIR = ROOT / "certificates"

K = int(os.environ.get("ITER_K", 6))
RHO = float(os.environ.get("ITER_RHO", 1e-6))
EPS = float(os.environ.get("ITER_EPS", 1e-9))

LOG2_3_UPPER = Fraction(1584962500721157, 10**15)
LOG2_3_F = float(LOG2_3_UPPER)
LAMBDA_F = LOG2_3_F - 1.0 + RHO


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


def main():
    t_overall = time.time()
    print(f"[071b] K={K} lambda={LAMBDA_F:.15f} eps={EPS}")

    n_res = 1 << K
    n_fibers = 1 << (3 * K)

    # Per-edge tracking: for each (E1, E2), max actual_drift, formula_drift,
    # S_edge, m_middle, pi_middle, max-fiber n_window_start (for diagnostics).
    edges = {}
    progress = max(1, n_fibers // 10)
    t0 = time.time()

    excess_max_global = -math.inf
    excess_max_edge = None

    for n0 in range(1, n_fibers):
        n_sim = int(n0)
        m0, n1, pi_0 = simulate_window(n_sim, K)
        r1 = n1 & (n_res - 1)

        # entering pi_middle window
        n_before_mid = n1
        m1, n2, pi_1 = simulate_window(n1, K)
        n_after_mid = n2
        r2 = n2 & (n_res - 1)
        E1 = (r1, pi_0, r2, pi_1)

        m2, n3, pi_2 = simulate_window(n2, K)
        r3 = n3 & (n_res - 1)
        E2 = (r2, pi_1, r3, pi_2)

        m_middle = m1
        S_middle = K - m_middle
        drift_formula = m_middle * (1.0 + LOG2_3_F) - K
        # Actual drift over the pi_middle window:
        if n_before_mid > 0:
            drift_actual = math.log2(n_after_mid / n_before_mid) if n_after_mid > 0 else -math.inf
        else:
            drift_actual = drift_formula
        excess = drift_actual - drift_formula

        key = (E1, E2)
        if key not in edges:
            edges[key] = {
                "m_middle": m_middle, "S_middle": S_middle,
                "drift_formula": drift_formula,
                "drift_actual_max": drift_actual,
                "drift_actual_min": drift_actual,
                "excess_max": excess,
                "n_before_mid_at_max": n_before_mid,
                "pi_middle": pi_1,
                "fiber_count": 1,
            }
        else:
            info = edges[key]
            info["fiber_count"] += 1
            if drift_actual > info["drift_actual_max"]:
                info["drift_actual_max"] = drift_actual
                info["n_before_mid_at_max"] = n_before_mid
                info["excess_max"] = excess
            if drift_actual < info["drift_actual_min"]:
                info["drift_actual_min"] = drift_actual
        if excess > excess_max_global:
            excess_max_global = excess
            excess_max_edge = (E1, E2, n_before_mid)

        if n0 % progress == 0:
            print(f"  fiber {n0:>10}/{n_fibers}  edges={len(edges):,}  "
                  f"max_excess_so_far={excess_max_global:.6f}  "
                  f"elapsed={time.time()-t0:.1f}s", flush=True)
    print(f"[071b] enumeration: {len(edges):,} edges in {time.time()-t0:.1f}s")
    print(f"[071b] max_excess (drift_actual - drift_formula) = "
          f"{excess_max_global:.6e}")

    # Load 068 certificate
    cert_path = CERT_DIR / f"iteration_068_certificate_K{K}.json"
    if not cert_path.exists():
        print(f"[071b] no 068 certificate at K={K}; aborting feasibility check")
        return
    cert = json.loads(cert_path.read_text())
    psi_floats = cert["psi"]

    state_set = set()
    for (E1, E2) in edges:
        state_set.add(E1); state_set.add(E2)
    states = sorted(state_set)
    state_to_idx = {s: i for i, s in enumerate(states)}
    n_states = len(states)
    if n_states != len(psi_floats):
        raise RuntimeError(
            f"state count mismatch: graph={n_states} psi={len(psi_floats)}; "
            f"068 cert may be out-of-sync; re-run 068 first"
        )

    # ---- Realised-trajectory LP feasibility check
    print(f"[071b] checking 068 psi against realised-trajectory drift ...")
    t0 = time.time()
    n_violated_actual = 0
    n_violated_formula_check = 0
    max_violation_actual = 0.0
    sample_violations = []
    for (E1, E2), info in edges.items():
        i1 = state_to_idx[E1]; i2 = state_to_idx[E2]
        d_actual_max = info["drift_actual_max"]
        d_formula = info["drift_formula"]
        S_e = info["S_middle"]
        rhs = LAMBDA_F * S_e - d_actual_max - EPS
        lhs = psi_floats[i2] - psi_floats[i1]
        viol = lhs - rhs
        if viol > 1e-9:
            n_violated_actual += 1
            if viol > max_violation_actual:
                max_violation_actual = viol
            if len(sample_violations) < 20:
                sample_violations.append({
                    "E1": list(E1), "E2": list(E2),
                    "S_edge": S_e, "drift_formula": d_formula,
                    "drift_actual_max": d_actual_max,
                    "excess": d_actual_max - d_formula,
                    "n_before_mid_at_max": info["n_before_mid_at_max"],
                    "violation": viol,
                })
        # Also check the formula-drift LP (068's original) as sanity
        rhs_formula = LAMBDA_F * S_e - d_formula - EPS
        if (lhs - rhs_formula) > 1e-9:
            n_violated_formula_check += 1
    t_check = time.time() - t0
    print(f"[071b] check done in {t_check:.1f}s")
    print(f"[071b] formula-LP violations (sanity) : {n_violated_formula_check}/{len(edges)}")
    print(f"[071b] realised-LP violations         : {n_violated_actual}/{len(edges)}")
    print(f"[071b] max realised-LP violation       : {max_violation_actual:.6e}")

    # ---- Re-solve LP using ACTUAL drift per edge (the realised LP)
    print(f"[071b] re-solving LP with drift_actual_max per edge ...")
    t0 = time.time()
    n_edges = len(edges)
    edge_list = list(edges.items())
    rows = np.empty(n_edges * 2, dtype=np.int64)
    cols = np.empty(n_edges * 2, dtype=np.int64)
    data = np.empty(n_edges * 2, dtype=np.float64)
    b_ub = np.empty(n_edges, dtype=np.float64)
    for i, ((E1, E2), info) in enumerate(edge_list):
        i1 = state_to_idx[E1]; i2 = state_to_idx[E2]
        rows[2*i] = i; cols[2*i] = i2; data[2*i] = 1.0
        rows[2*i+1] = i; cols[2*i+1] = i1; data[2*i+1] = -1.0
        b_ub[i] = LAMBDA_F * info["S_middle"] - info["drift_actual_max"] - EPS
    A_ub = coo_matrix((data, (rows, cols)), shape=(n_edges, n_states)).tocsr()
    bounds = [(None, None)] * n_states
    bounds[0] = (0.0, 0.0)
    c_obj = np.zeros(n_states)
    res_realised = linprog(
        c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs"
    )
    t_realised = time.time() - t0
    print(f"[071b] realised-LP HiGHS: {res_realised.message}  "
          f"solve={t_realised:.1f}s  feasible={res_realised.success}")
    realised_min_margin = None
    realised_max_margin = None
    if res_realised.success:
        m_arr = b_ub - A_ub.dot(res_realised.x)
        realised_min_margin = float(m_arr.min())
        realised_max_margin = float(m_arr.max())
        print(f"[071b] realised-LP min_margin={realised_min_margin:.3e}  "
              f"max_margin={realised_max_margin:.3e}")

    # ---- Excess drift histogram
    excess_hist = Counter()
    for info in edges.values():
        # Bucket excess into multiples of 0.001 (per fiber edge), capped
        excess = info["excess_max"]
        # Use log-scale bucketing
        if excess <= 0:
            bucket = "le_0"
        elif excess < 1e-6:
            bucket = "lt_1e-6"
        elif excess < 1e-4:
            bucket = "lt_1e-4"
        elif excess < 1e-2:
            bucket = "lt_1e-2"
        elif excess < 0.1:
            bucket = "lt_0.1"
        elif excess < 1.0:
            bucket = "lt_1.0"
        else:
            bucket = "ge_1.0"
        excess_hist[bucket] += 1

    proof_state = {
        "proof_state": "iteration_071b_realized_trajectory_restriction",
        "K": K,
        "lambda_global_float": LAMBDA_F,
        "epsilon": EPS,
        "rho_padding": RHO,
        "n_edges": len(edges),
        "n_states": n_states,
        "max_excess_drift_actual_minus_formula": excess_max_global,
        "excess_at_edge": (
            None if excess_max_edge is None else
            {"E1": list(excess_max_edge[0]), "E2": list(excess_max_edge[1]),
             "n_before_mid": int(excess_max_edge[2])}
        ),
        "excess_histogram": dict(excess_hist),
        "n_realised_LP_violations_using_068_psi": n_violated_actual,
        "n_formula_LP_violations_sanity_check": n_violated_formula_check,
        "max_realised_LP_violation": max_violation_actual,
        "realised_LP_satisfied_by_068_psi": n_violated_actual == 0,
        "realised_LP_resolved_feasible": bool(res_realised.success),
        "realised_LP_scipy_message": str(res_realised.message),
        "realised_LP_min_margin": realised_min_margin,
        "realised_LP_max_margin": realised_max_margin,
        "sample_violations": sample_violations,
        "elapsed_total_seconds": time.time() - t_overall,
        "interpretation": (
            "The realised-trajectory LP uses drift_actual(n) = "
            "log_2(T_pi(n) / n) per edge, which exceeds the formula "
            "drift by log_2(1 + B_pi / (3^m * n)) for each fiber "
            "value n. We test whether the 068 psi (built using "
            "formula drift) ALSO satisfies the realised-trajectory "
            "LP: psi(E2) - psi(E1) <= lambda*S - drift_actual_max - "
            "eps. If yes, the certificate is robust to actual "
            "integer dynamics, not just an aggregation. If no, the "
            "violating edges identify where the formula LP was "
            "optimistic; we need either a new psi or an additional "
            "term in the certificate."
        ),
    }
    out = PROOF_DIR / f"iteration_071b_realized_trajectory_K{K}.json"
    out.write_text(json.dumps(proof_state, indent=2))
    print(f"[071b] wrote {out}")


if __name__ == "__main__":
    main()
