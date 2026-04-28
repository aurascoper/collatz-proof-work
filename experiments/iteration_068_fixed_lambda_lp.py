"""Iteration 068: positivity-aware fixed-lambda psi-only LP.

Following 067, we use a *fixed* scalar

    lambda_global = LOG2_3_UPPER - 1 + rho      (rho = 1e-6 default)

as the eta-fuel coefficient. This contracts every artefact cycle in
ordinary Collatz at even K (per 067's parity-induced upper bound
drift/S <= log_2 3 - 1).

Per-edge LP constraint (correct sign per Phi = log_2(n) + lambda*eta + psi):

    Phi(n+1) - Phi(n) = drift_edge - lambda * S_edge + (psi[E2] - psi[E1])

We require Phi to decrease by at least EPSILON each transition:

    psi[E2] - psi[E1] - lambda * S_edge <= -drift_edge - EPSILON,
i.e.,
    psi[E2] - psi[E1] <= lambda * S_edge - drift_edge - EPSILON.

Variables: psi[E] for each edge state E. (No per-state lam this time.)
Anchor: psi[0] = 0.
Objective: zero (screening LP).

Per-edge data:
    drift_edge = m_middle * (1 + log_2 3) - K
    S_edge     = K - m_middle

(m_middle is popcount(pi_1) where E1 = (r1, pi_0, r2, pi_1).)

If the LP is feasible, we have a *positivity-aware* descent
certificate at the current K. Per 067 the cycle-level necessary
condition is satisfied for every cycle in any abstract graph derived
from ordinary Collatz at even K, so this LP should be feasible. If
it isn't, the BF cycle witness must show drift/S > lambda_global
(unlikely given 067) or the formulation has a bug.
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

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix


K = int(os.environ.get("ITER_K", 8))
EPSILON = float(os.environ.get("ITER_EPS", 1e-9))
RHO = float(os.environ.get("ITER_RHO", 1e-6))

ROOT = Path(__file__).resolve().parent.parent
PROOF_DIR = ROOT / "proof_states"
WITNESS_DIR = ROOT / "witnesses"
CERT_DIR = ROOT / "certificates"
for d in (PROOF_DIR, WITNESS_DIR, CERT_DIR):
    d.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / "verifiers"))
from cycle_classifier import classify_cycle  # noqa: E402

LOG2_3_UPPER = Fraction(1584962500721157, 10**15)
LOG2_3_FLOAT = float(LOG2_3_UPPER)
LAMBDA_GLOBAL = LOG2_3_FLOAT - 1.0 + RHO  # screening float
LAMBDA_GLOBAL_Q = LOG2_3_UPPER - 1 + Fraction(int(RHO * 10**15), 10**15)


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


def enumerate_edges(K: int):
    n_res = 1 << K
    n_fibers = 1 << (3 * K)
    aff = {}
    for r in range(n_res):
        A, B, denom = affine_constants(r, K)
        m, _, mask = simulate_window(r, K)
        aff[mask] = (B, denom, m)

    edges = {}
    progress = max(1, n_fibers // 10)
    t0 = time.time()
    for n0 in range(1, n_fibers):
        n_sim = int(n0)
        m0, n1, pi_0 = simulate_window(n_sim, K)
        r1 = n1 & (n_res - 1)
        m1, n2, pi_1 = simulate_window(n1, K)
        r2 = n2 & (n_res - 1)
        E1 = (r1, pi_0, r2, pi_1)

        m2, n3, pi_2 = simulate_window(n2, K)
        r3 = n3 & (n_res - 1)
        E2 = (r2, pi_1, r3, pi_2)

        m_middle = m1
        S_middle = K - m_middle
        drift = m_middle * (1.0 + LOG2_3_FLOAT) - K
        # No more c_val; key by (E1, E2). Drift uniquely determined by pi_1
        # which sits in E1 -- so all parallel fibers agree.
        key = (E1, E2)
        if key not in edges:
            edges[key] = {
                "drift_float": drift,
                "m_middle": m_middle,
                "S_middle": S_middle,
                "pi_middle": pi_1,
                "n_example": n_sim,
            }
        if n0 % progress == 0:
            print(
                f"  enumerated {n0:>10}/{n_fibers}  edges={len(edges):,}  "
                f"elapsed={time.time()-t0:.1f}s",
                flush=True,
            )
    print(f"[068] enumeration: {len(edges):,} edges in {time.time()-t0:.1f}s")
    return edges


def build_lp(edges):
    state_set = set()
    for (E1, E2) in edges:
        state_set.add(E1); state_set.add(E2)
    states = sorted(state_set)
    state_to_idx = {s: i for i, s in enumerate(states)}
    n_states = len(states)
    n_edges = len(edges)
    n_vars = n_states  # psi only

    rows = np.empty(n_edges * 2, dtype=np.int64)
    cols = np.empty(n_edges * 2, dtype=np.int64)
    data = np.empty(n_edges * 2, dtype=np.float64)
    b_ub = np.empty(n_edges, dtype=np.float64)

    edge_list = list(edges.items())
    for i, ((E1, E2), info) in enumerate(edge_list):
        i1 = state_to_idx[E1]; i2 = state_to_idx[E2]
        rows[2*i] = i; cols[2*i] = i2; data[2*i] = 1.0
        rows[2*i+1] = i; cols[2*i+1] = i1; data[2*i+1] = -1.0
        # psi[i2] - psi[i1] <= lambda*S_edge - drift_edge - eps
        b_ub[i] = LAMBDA_GLOBAL * info["S_middle"] - info["drift_float"] - EPSILON

    A_ub = coo_matrix((data, (rows, cols)), shape=(n_edges, n_vars)).tocsr()
    bounds = [(None, None)] * n_states
    bounds[0] = (0.0, 0.0)  # psi[0] = 0 anchor
    c = np.zeros(n_vars)

    return {
        "A_ub": A_ub, "b_ub": b_ub, "c": c, "bounds": bounds,
        "states": states, "state_to_idx": state_to_idx,
        "n_states": n_states, "n_edges": n_edges,
        "edge_list": edge_list,
    }


def extract_cycle_witness(lp, edges):
    """If LP infeasible, find a negative cycle in the residual graph.

    Edge weight: w_e = drift_e - lambda*S_e + EPSILON. A NEGATIVE cycle
    proves infeasibility (psi can't satisfy). Equivalently this asks
    whether sum (drift_e - lambda*S_e) > -L*eps, i.e., whether
    drift_total - lambda * S_total > -L*eps. Per 067 this should NEVER
    happen if drift_total/S_total <= lambda. So extracting a witness
    here is itself a notable result.
    """
    n_states = lp["n_states"]
    edge_list = lp["edge_list"]
    state_to_idx = lp["state_to_idx"]

    m = len(edge_list)
    s1 = np.zeros(m, dtype=np.int64)
    s2 = np.zeros(m, dtype=np.int64)
    w = np.zeros(m, dtype=np.float64)
    for i, ((E1, E2), info) in enumerate(edge_list):
        s1[i] = state_to_idx[E1]
        s2[i] = state_to_idx[E2]
        w[i] = info["drift_float"] - LAMBDA_GLOBAL * info["S_middle"] + EPSILON

    dist = np.zeros(n_states, dtype=np.float64)
    pred_node = np.full(n_states, -1, dtype=np.int64)
    pred_edge = np.full(n_states, -1, dtype=np.int64)
    BUDGET = 200
    last_relaxed = -1
    for it in range(BUDGET):
        # Reverse-direction BF: we want sum(drift - lambda*S) along a closed
        # walk to be > -L*eps. Equivalently negative cycle in -w_e.
        cand = dist[s1] - w
        improved = cand < dist[s2] - 1e-12
        if not np.any(improved):
            return None
        imp = np.where(improved)[0]
        dist[s2[imp]] = cand[imp]
        pred_node[s2[imp]] = s1[imp]
        pred_edge[s2[imp]] = imp
        if it == BUDGET - 1:
            last_relaxed = int(s2[imp[0]])

    if last_relaxed == -1:
        return None
    v = last_relaxed
    for _ in range(BUDGET):
        v = int(pred_node[v])
        if v == -1:
            return None
    cycle_start = v; cur = cycle_start
    path_idx = []
    for _ in range(BUDGET + 5):
        e_idx = int(pred_edge[cur])
        if e_idx < 0:
            return None
        path_idx.append(e_idx)
        cur = int(pred_node[cur])
        if cur == cycle_start:
            break
    path_idx.reverse()
    return path_idx


def main():
    overall_t0 = time.time()
    print(f"[068] starting K={K} eps={EPSILON} rho={RHO} "
          f"lambda_global={LAMBDA_GLOBAL:.15f}")
    edges = enumerate_edges(K)

    print(f"[068] building LP ...")
    t0 = time.time()
    lp = build_lp(edges)
    t_build = time.time() - t0
    print(f"[068] LP: n_states={lp['n_states']:,} n_edges={lp['n_edges']:,} "
          f"build={t_build:.1f}s")

    t0 = time.time()
    res = linprog(
        lp["c"], A_ub=lp["A_ub"], b_ub=lp["b_ub"],
        bounds=lp["bounds"], method="highs",
    )
    t_solve = time.time() - t0
    print(f"[068] HiGHS: status={res.status} success={res.success} "
          f"msg={res.message}  solve={t_solve:.1f}s")

    proof_state = {
        "proof_state": "iteration_068_fixed_lambda_fuel_lp",
        "K": K,
        "epsilon": EPSILON,
        "rho_padding": RHO,
        "lambda_global_float": LAMBDA_GLOBAL,
        "lambda_global_str": str(LAMBDA_GLOBAL_Q),
        "lambda_formula": "LOG2_3_UPPER - 1 + rho",
        "log2_3_upper_rational": [LOG2_3_UPPER.numerator, LOG2_3_UPPER.denominator],
        "state_model": "2-window edge state E = (r1, pi0, r2, pi1)",
        "n_unique_states": lp["n_states"],
        "n_unique_edges": lp["n_edges"],
        "scipy_status": int(res.status),
        "scipy_message": str(res.message),
        "lp_feasible": bool(res.success),
        "elapsed_enum_seconds": None,
        "elapsed_lp_build_seconds": t_build,
        "elapsed_lp_solve_seconds": t_solve,
    }
    if res.success:
        margins = lp["b_ub"] - lp["A_ub"].dot(res.x)
        proof_state["min_margin"] = float(margins.min())
        proof_state["max_margin"] = float(margins.max())
        # Save certificate.
        cert = {
            "proof_state": "iteration_068_certificate",
            "K": K,
            "lambda_global_str": str(LAMBDA_GLOBAL_Q),
            "n_states": lp["n_states"],
            "psi": res.x.tolist(),
        }
        cert_path = CERT_DIR / f"iteration_068_certificate_K{K}.json"
        cert_path.write_text(json.dumps(cert))
        proof_state["certificate_file"] = str(cert_path.relative_to(ROOT))
        proof_state["interpretation"] = (
            "Fixed-lambda psi-only LP feasible at K=" + str(K) + ". This "
            "demonstrates a positivity-aware descent certificate exists "
            "in the 2-window edge-state abstraction with lambda = "
            "log_2(3) - 1 + rho. NOT yet a Collatz proof; we still need: "
            "(a) exact rational re-verification of every constraint, "
            "(b) closing the abstraction gap via realized-trajectory "
            "verification, and (c) extending K to scale beyond 8."
        )
    else:
        path = extract_cycle_witness(lp, edges)
        if path is not None:
            cycle_drift = sum(lp["edge_list"][i][1]["drift_float"] for i in path)
            cycle_S = sum(lp["edge_list"][i][1]["S_middle"] for i in path)
            cycle_corrected = cycle_drift - LAMBDA_GLOBAL * cycle_S
            pi_mids = [lp["edge_list"][i][1]["pi_middle"] for i in path]
            cls = classify_cycle(pi_mids, K)
            wit = {
                "K": K,
                "iteration": "068",
                "lambda_global": LAMBDA_GLOBAL,
                "cycle_length": len(path),
                "cycle_total_drift": cycle_drift,
                "cycle_total_even_steps_S": cycle_S,
                "cycle_total_corrected_drift_minus_lambda_S": cycle_corrected,
                "classification": cls,
                "edges": [
                    {
                        "E1": list(lp["edge_list"][i][0][0]),
                        "E2": list(lp["edge_list"][i][0][1]),
                        "pi_middle_int": int(lp["edge_list"][i][1]["pi_middle"]),
                        "pi_middle_bin": format(int(lp["edge_list"][i][1]["pi_middle"]), f"0{K}b"),
                        "m_middle": int(lp["edge_list"][i][1]["m_middle"]),
                        "S_middle": int(lp["edge_list"][i][1]["S_middle"]),
                        "drift_float": float(lp["edge_list"][i][1]["drift_float"]),
                    }
                    for i in path
                ],
            }
            wit_path = WITNESS_DIR / f"iteration_068_cycle_K{K}.json"
            wit_path.write_text(json.dumps(wit, indent=2))
            proof_state["witness_file"] = str(wit_path.relative_to(ROOT))
            proof_state["if_infeasible_cycle"] = {
                "cycle_length": len(path),
                "cycle_total_drift": cycle_drift,
                "cycle_total_even_steps_S": cycle_S,
                "cycle_total_corrected": cycle_corrected,
                "classification": cls.get("classification"),
                "candidate_n": cls.get("candidate_n"),
                "denom": cls.get("denom_2S_minus_3m"),
            }
            proof_state["interpretation"] = (
                "Fixed-lambda psi-only LP infeasible at K=" + str(K) + ". "
                "Per 067, this should be impossible if every cycle has "
                "drift/S <= log_2 3 - 1. The witness exposes either (a) a "
                "cycle violating the parity bound (would invalidate 067), "
                "(b) a numerical/floating-point issue (use exact rational "
                "verifier), or (c) a missing constraint structure."
            )
        else:
            proof_state["interpretation"] = (
                "LP infeasible but no BF witness found within budget. "
                "Likely a numerical artefact; investigate."
            )

    proof_state["total_elapsed_seconds"] = time.time() - overall_t0
    out = PROOF_DIR / f"iteration_068_fixed_lambda_K{K}.json"
    out.write_text(json.dumps(proof_state, indent=2))
    print(f"[068] wrote {out}")
    print(json.dumps(
        {k: v for k, v in proof_state.items() if k not in ("rounds",)}, indent=2
    ))


if __name__ == "__main__":
    main()
