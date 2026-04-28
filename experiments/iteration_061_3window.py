"""Iteration 061: 3-window trajectory-consistent edge-state LP at K=8.

Triggered when 060c remains infeasible *and* the witness is depth-free
(i.e. lam-independent). The hypothesis is that the 2-window state
abstraction admits cycles no integer trajectory realises (e.g. the K=6
self-loop at (r=63, pi=101010) whose affine fixed point is n=-1).

A 3-window state encodes three consecutive (r, pi) pairs. Transitions
simulate one new window and shift the buffer. This is identical to the
sketch in cell 66 of the working notebook, refactored into a script and
adapted to the 060c grouping discipline:

  - States are S = (r1, pi0, r2, pi1, r3, pi2).
  - Transitions S1 -> S2 are produced by simulating one extra window W3
    that takes r3 -> r4 with mask pi3.
  - Drift attached to pi_middle = pi_2 (the middle window of S1, which is
    the one being executed when S1 -> S2 fires).
  - Edges grouped by (S1, S2, c_val).
  - LP discipline identical to 060c.

Caveat: at K=8, exhaustive 4-window enumeration covers `n0 mod 2^32` =
4.29B fibers. We sample first (configurable) to gauge feasibility. A
full closure would require Numba/C++ acceleration.

Run with:
    ITER_K=8 ITER_RANDOM_SAMPLES=10000000 python3 experiments/iteration_061_3window.py
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verifiers"))
from cycle_classifier import classify_cycle  # noqa: E402


K = int(os.environ.get("ITER_K", 8))
EPSILON = float(os.environ.get("ITER_EPS", 1e-2))
LAM_UB = float(os.environ.get("ITER_LAM_UB", 128.0))
RANDOM_SAMPLES = int(os.environ.get("ITER_RANDOM_SAMPLES", 10_000_000))
RANDOM_SEED = 42
DELTA_SAT = 64

ROOT = Path(__file__).resolve().parent.parent
PROOF_DIR = ROOT / "proof_states"
WITNESS_DIR = ROOT / "witnesses"
CERT_DIR = ROOT / "certificates"
for d in (PROOF_DIR, WITNESS_DIR, CERT_DIR):
    d.mkdir(parents=True, exist_ok=True)

LOG2_3_FLOAT = math.log2(3.0)
LOG2_3_UPPER = Fraction(1584962500721157, 10**15)


def simulate_window(n: int, k: int):
    m = 0
    curr = n
    mask = 0
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
            B = 3 * B + (1 << S)
            A = 3 * A
            n = 3 * n + 1
        else:
            S += 1
            n //= 2
    if (A * r + B) != n * (1 << S):
        raise AssertionError(f"affine recurrence != simulation r={r}")
    denom = (1 << S) - A
    return A, B, denom


def v2_int(val: int, cap: int = DELTA_SAT) -> int:
    if val == 0:
        return cap
    val = abs(val)
    raw = (val & -val).bit_length() - 1
    return raw if raw < cap else cap


def main():
    t0 = time.time()
    n_res = 1 << K

    aff = []
    mask_to_r = {}
    for r in range(n_res):
        A, B, denom = affine_constants(r, K)
        m, _, mask = simulate_window(r, K)
        aff.append((B, denom, mask, m))
        mask_to_r[mask] = r

    edges = {}
    rng = np.random.default_rng(RANDOM_SEED)
    seeds = rng.integers(1, 1 << (4 * K + 4), size=RANDOM_SAMPLES, dtype=np.int64)

    progress = max(1, RANDOM_SAMPLES // 20)
    for i, seed in enumerate(seeds):
        n = int(seed)

        m0, n1, pi0 = simulate_window(n, K)
        r1 = n1 & (n_res - 1)

        m1, n2, pi1 = simulate_window(n1, K)
        r2 = n2 & (n_res - 1)

        m2, n3, pi2 = simulate_window(n2, K)
        r3 = n3 & (n_res - 1)
        B2, den2, _, _ = aff[mask_to_r[pi2]]
        delta_1 = v2_int(n3 * den2 - B2)

        S1 = (r1, pi0, r2, pi1, r3, pi2)

        m3, n4, pi3 = simulate_window(n3, K)
        r4 = n4 & (n_res - 1)
        B3, den3, _, _ = aff[mask_to_r[pi3]]
        delta_2 = v2_int(n4 * den3 - B3)

        S2 = (r2, pi1, r3, pi2, r4, pi3)

        # pi_middle here is pi_2 (the middle of S1 = the executed window)
        m_middle = m2
        c_val = delta_2 - delta_1
        drift = m_middle * (1.0 + LOG2_3_FLOAT) - K

        key = (S1, S2, c_val)
        if key not in edges:
            edges[key] = {
                "drift_float": drift,
                "m_middle": m_middle,
                "pi_middle": pi2,
                "n_example": n,
                "count": 0,
            }
        edges[key]["count"] += 1

        if (i + 1) % progress == 0:
            print(
                f"  {i+1:>10}/{RANDOM_SAMPLES} samples, edges={len(edges):,}, "
                f"elapsed={time.time()-t0:.1f}s",
                flush=True,
            )

    enum_secs = time.time() - t0
    print(f"[061] enumeration: {len(edges):,} edges in {enum_secs:.1f}s")

    state_set = set()
    for (S1, S2, _) in edges:
        state_set.add(S1); state_set.add(S2)
    states = sorted(state_set)
    state_to_idx = {s: i for i, s in enumerate(states)}
    n_states = len(states)
    n_edges = len(edges)
    n_vars = 2 * n_states

    rows = []; cols = []; data = []
    b_ub = np.zeros(n_edges, dtype=np.float64)
    edge_list = list(edges.items())
    for i, ((S1, S2, c_val), inf) in enumerate(edge_list):
        i1 = state_to_idx[S1]; i2 = state_to_idx[S2]
        rows.append(i); cols.append(i2); data.append(1.0)
        rows.append(i); cols.append(i1); data.append(-1.0)
        rows.append(i); cols.append(n_states + i2); data.append(float(c_val))
        b_ub[i] = -inf["drift_float"] - EPSILON

    A_ub = coo_matrix(
        (np.array(data), (np.array(rows), np.array(cols))),
        shape=(n_edges, n_vars),
    ).tocsr()

    bounds = [(None, None)] * n_states + [(0.0, LAM_UB)] * n_states
    bounds[0] = (0.0, 0.0)
    c = np.zeros(n_vars)

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

    proof_state = {
        "proof_state": "iteration_061_k8_3window_cval_split",
        "K": K,
        "epsilon": EPSILON,
        "lam_upper_bound": LAM_UB,
        "log2_3_upper_rational": [LOG2_3_UPPER.numerator, LOG2_3_UPPER.denominator],
        "exhaustive": False,
        "random_samples": RANDOM_SAMPLES,
        "n_unique_states": n_states,
        "n_unique_cval_split_edges": n_edges,
        "scipy_status": int(res.status),
        "scipy_message": str(res.message),
        "lp_feasible": bool(res.success),
        "closed_graph": False,
        "drift_assignment": "pi_middle = pi_2 (middle of S1; executed window)",
        "monotonicity_constraint_on_lambda": False,
        "elapsed_total_seconds": time.time() - t0,
    }
    if res.success:
        margins = b_ub - A_ub.dot(res.x)
        proof_state["if_feasible_min_margin"] = float(margins.min())
        proof_state["if_feasible_max_margin"] = float(margins.max())
        # Export certificate (psi, lam only; states recomputable from script).
        cert = {
            "proof_state": "iteration_061_certificate",
            "K": K,
            "n_states": n_states,
            "n_edges": n_edges,
            "psi": res.x[:n_states].tolist(),
            "lam": res.x[n_states:].tolist(),
            "min_margin": float(margins.min()),
            "max_margin": float(margins.max()),
            "sampled_not_closed": True,
            "random_seed": RANDOM_SEED,
            "random_samples": RANDOM_SAMPLES,
        }
        cert_path = CERT_DIR / f"iteration_061_certificate_K{K}_S{RANDOM_SAMPLES}.json"
        cert_path.write_text(json.dumps(cert))
        proof_state["certificate_file"] = str(cert_path.relative_to(ROOT))
        proof_state["interpretation"] = (
            "3-window LP feasible on a sampled multigraph. NOT a closed-graph "
            "result -- only a *necessary* condition for a closed 3-window "
            "certificate. To upgrade to a closed result, exhaustively enumerate "
            "n0 mod 2^{4K} (or prove closure via affine residue structure)."
        )
    else:
        # ---- 3-window depth-free Bellman-Ford witness
        BF_MAX_ITERS = int(os.environ.get("ITER_BF_MAX_ITERS", 200))
        # Reduce parallel edges per (i1, i2) to one edge, taking max c_val.
        edge_max = {}
        for (S1, S2, c_val), info in edges.items():
            i1 = state_to_idx[S1]; i2 = state_to_idx[S2]
            key = (i1, i2)
            d = info["drift_float"]
            if key not in edge_max or c_val > edge_max[key]["c_val"]:
                edge_max[key] = {
                    "c_val": c_val, "drift": d,
                    "S1": S1, "S2": S2, "info": info,
                }

        edges_bf = list(edge_max.items())
        m_e = len(edges_bf)
        s1 = np.zeros(m_e, dtype=np.int64)
        s2 = np.zeros(m_e, dtype=np.int64)
        w_arr = np.zeros(m_e, dtype=np.float64)
        for k_, ((i1, i2), v) in enumerate(edges_bf):
            s1[k_] = i1; s2[k_] = i2
            w_arr[k_] = -v["drift"] - EPSILON  # depth-free abstraction

        dist = np.zeros(n_states, dtype=np.float64)
        pred_node = np.full(n_states, -1, dtype=np.int64)
        pred_edge = np.full(n_states, -1, dtype=np.int64)
        budget = min(BF_MAX_ITERS, n_states)
        last_relaxed = -1
        for it in range(budget):
            cand = dist[s1] + w_arr
            improved = cand < dist[s2] - 1e-12
            if not np.any(improved):
                break
            imp = np.where(improved)[0]
            dist[s2[imp]] = cand[imp]
            pred_node[s2[imp]] = s1[imp]
            pred_edge[s2[imp]] = imp
            if it == budget - 1:
                last_relaxed = int(s2[imp[0]])

        cycle_payload = None
        if last_relaxed != -1:
            v = last_relaxed
            for _ in range(budget):
                v = int(pred_node[v])
                if v == -1:
                    v = -1; break
            if v != -1:
                cycle_start = v
                path = []
                cur = cycle_start
                for _ in range(budget + 5):
                    e_idx = int(pred_edge[cur])
                    if e_idx < 0:
                        break
                    (i1, i2), pkg = edges_bf[e_idx]
                    path.append(pkg)
                    cur = int(pred_node[cur])
                    if cur == cycle_start:
                        break
                tot_drift = sum(p["drift"] for p in path)
                tot_dep = sum(p["c_val"] for p in path)
                # Try integer-realisability via concatenated pi_middle bits.
                bits = []
                for p in path:
                    pi = p["info"]["pi_middle"]
                    for j in range(K - 1, -1, -1):
                        bits.append((pi >> j) & 1)
                A2, B2, S2v = 1, 0, 0
                for b in bits:
                    if b == 1:
                        B2 = 3 * B2 + (1 << S2v); A2 = 3 * A2
                    else:
                        S2v += 1
                denom_cyc = (1 << S2v) - A2
                realised = False; n_val = None
                if denom_cyc != 0 and B2 % denom_cyc == 0:
                    n_val = B2 // denom_cyc
                    realised = n_val > 0
                pi_middles_for_cls = [p["info"]["pi_middle"] for p in path]
                cls = classify_cycle(pi_middles_for_cls, K)
                cycle_payload = {
                    "cycle_length": len(path),
                    "cycle_total_drift": float(tot_drift),
                    "cycle_total_depth_effect": int(tot_dep),
                    "integer_realizable_single_orbit": bool(realised),
                    "realised_n_value": (None if n_val is None else int(n_val)),
                    "realised_denom": int(denom_cyc),
                    "realised_num": int(B2),
                    "classification": cls,
                    "cycle_edges": [
                        {
                            "S1": list(p["S1"]),
                            "S2": list(p["S2"]),
                            "pi_middle": f"{p['info']['pi_middle']:0{K}b}",
                            "m_middle": int(p["info"]["m_middle"]),
                            "drift_float": float(p["drift"]),
                            "c_val": int(p["c_val"]),
                            "n_example": int(p["info"]["n_example"]),
                        } for p in path
                    ],
                }
                wit_path = WITNESS_DIR / f"iteration_061_cycle_K{K}_S{RANDOM_SAMPLES}.json"
                wit_path.write_text(json.dumps({
                    "K": K,
                    "iteration": "061",
                    "random_samples": RANDOM_SAMPLES,
                    "depth_free_witness": cycle_payload,
                    "interpretation": (
                        "Bellman-Ford on the depth-free abstraction of the "
                        "3-window c_val-split sampled graph. A negative "
                        "cycle here makes the SAMPLED LP infeasible. It "
                        "does NOT necessarily prove the closed 3-window LP "
                        "is infeasible -- the closed graph contains all "
                        "fibers, including ones that may break this cycle."
                    ),
                }, indent=2))
                proof_state["witness_file"] = str(wit_path.relative_to(ROOT))
                proof_state["depth_free_cycle_total_drift"] = cycle_payload["cycle_total_drift"]
                proof_state["depth_free_cycle_length"] = cycle_payload["cycle_length"]
                proof_state["depth_free_cycle_integer_realizable_single_orbit"] = (
                    cycle_payload["integer_realizable_single_orbit"]
                )

        proof_state["witness_extracted"] = cycle_payload is not None
        proof_state["interpretation"] = (
            "3-window LP infeasible on a sampled multigraph. " +
            ("Depth-free cycle witness extracted; "
             "if integer-realizable, this is a real obstruction to the "
             "*sampled* LP only and may or may not survive in the closed "
             "graph. Closure still requires either exhaustive enumeration "
             "over n0 mod 2^{4K} or a deductive argument."
             if cycle_payload is not None else
             "Witness extraction failed (no negative cycle detected within "
             "BF budget). The infeasibility may involve the depth Lyapunov "
             "term in a subtle way; consider extending BF to lam-friendliest.")
        )

    out = PROOF_DIR / f"iteration_061_3window_K{K}.json"
    out.write_text(json.dumps(proof_state, indent=2))
    print(f"[061] wrote {out}")
    print(json.dumps(proof_state, indent=2))


if __name__ == "__main__":
    main()
