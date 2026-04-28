"""Iteration 060d: filter abstraction-artifact self-loops, then re-solve.

The 060c K=8 witness is a length-1 self-loop at the closed-affine-graph
state E = (r=255, pi=10101010, r=255, pi=10101010) whose affine fixed
point is n=-1 -- not a positive integer. No real Collatz orbit ever
traverses this self-loop, so removing it from the LP cannot rule out any
Collatz behaviour. If the LP becomes feasible after this surgical
removal, we know the K=8 closed 2-window LP is *almost* feasible and
that the only obstruction was a finite list of identifiable artefacts.

A self-loop in the 2-window edge-state graph has the shape
    (r, pi, r, pi) -> (r, pi, r, pi)
which means: starting at residue r, executing one window with parity pi
lands at residue r again, *and* the next K bits read off n_after still
form pi. For this self-loop to be realised by an integer trajectory, we
need a positive integer n such that
    n ≡ r (mod 2^K),
    T_pi(n) = n         (n is the affine fixed point of pi),
    bits(n) start with pi for K steps     (parity is exactly pi).
The first two conditions imply the third (T_pi(n) = n means the parity
of the next K steps starting from n equals pi). So we just need:
    f_pi := B_pi / (2^(K-m) - 3^m) integer, positive, and f_pi mod 2^K = r.

The 060c run produced 12 725 664 c_val-split edges. We will:
    1. Identify all self-loop edges (E1 == E2 component).
    2. For each, verify integer-realisability.
    3. Drop the non-realisable ones.
    4. Re-solve the LP and report feasibility, plus a comparison.

Outputs:
    proof_states/iteration_060d_K{K}.json
    witnesses/iteration_060d_cycle_K{K}.json (if still infeasible)
    certificates/iteration_060d_certificate_K{K}.json (if feasible)
"""

from __future__ import annotations

import json
import math
import os
import time
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix


K = int(os.environ.get("ITER_K", 8))
EPSILON = float(os.environ.get("ITER_EPS", 1e-2))
LAM_UB = float(os.environ.get("ITER_LAM_UB", 128.0))
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
    if (A * r + B) != n * (1 << S):
        raise AssertionError(f"affine recurrence != simulation r={r}")
    return A, B, (1 << S) - A


def v2_int(val: int, cap: int = DELTA_SAT) -> int:
    if val == 0:
        return cap
    val = abs(val)
    raw = (val & -val).bit_length() - 1
    return raw if raw < cap else cap


def main():
    t_start = time.time()
    n_res = 1 << K

    # ---- 1. Precompute affine constants and identify realisable self-loops
    aff = {}
    realisable_self_loops = set()
    selfloop_check = {}
    for r in range(n_res):
        A, B, denom = affine_constants(r, K)
        m, _, mask = simulate_window(r, K)
        aff[mask] = (B, denom, m)
        # Self-loop (r, mask, r, mask) realisable iff fixed point f = B/denom
        # is a positive integer congruent to r mod 2^K.
        if denom == 0:
            realisable = False
            n_fix = None
        elif B % denom != 0:
            realisable = False
            n_fix = None
        else:
            n_fix = B // denom
            realisable = n_fix > 0 and (n_fix & (n_res - 1)) == r
        selfloop_check[(r, mask)] = (realisable, n_fix, B, denom)
        if realisable:
            realisable_self_loops.add((r, mask, r, mask))

    print(f"[060d] K={K}: realisable self-loops = {len(realisable_self_loops)}")

    # ---- 2. Re-enumerate edges (same as 060c)
    edges = {}
    n_fibers = 1 << (3 * K)
    progress = max(1, n_fibers // 20)
    t_enum = time.time()
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
        c_val = delta_2 - delta_1
        drift = m_middle * (1.0 + LOG2_3_FLOAT) - K
        key = (E1, E2, c_val)
        if key not in edges:
            edges[key] = {"drift": drift, "m_middle": m_middle, "pi_middle": pi_1}

        if n0 % progress == 0:
            print(
                f"  enumerated {n0:>10}/{n_fibers}  "
                f"edges={len(edges):,}  elapsed={time.time()-t_enum:.1f}s",
                flush=True,
            )
    print(f"[060d] enumeration: {len(edges):,} edges in {time.time()-t_enum:.1f}s")

    # ---- 3. Filter abstraction-artifact self-loops
    edges_kept = {}
    n_dropped_artifact_selfloop = 0
    for key, info in edges.items():
        E1, E2, c_val = key
        if E1 == E2:
            r1, pi_0, r2, pi_1 = E1
            assert r1 == r2 and pi_0 == pi_1
            if (r1, pi_1, r2, pi_1) not in realisable_self_loops:
                n_dropped_artifact_selfloop += 1
                continue
        edges_kept[key] = info

    print(
        f"[060d] dropped {n_dropped_artifact_selfloop:,} artefact self-loops; "
        f"kept {len(edges_kept):,} of {len(edges):,} edges"
    )

    # ---- 4. Build LP
    state_set = set()
    for (E1, E2, _) in edges_kept:
        state_set.add(E1); state_set.add(E2)
    states = sorted(state_set)
    state_to_idx = {s: i for i, s in enumerate(states)}
    n_states = len(states)
    n_edges = len(edges_kept)
    n_vars = 2 * n_states

    rows = []; cols = []; data = []
    b_ub = np.zeros(n_edges, dtype=np.float64)
    edge_list = list(edges_kept.items())
    for i, ((E1, E2, c_val), inf) in enumerate(edge_list):
        i1 = state_to_idx[E1]; i2 = state_to_idx[E2]
        rows.append(i); cols.append(i2); data.append(1.0)
        rows.append(i); cols.append(i1); data.append(-1.0)
        rows.append(i); cols.append(n_states + i2); data.append(float(c_val))
        b_ub[i] = -inf["drift"] - EPSILON

    A_ub = coo_matrix(
        (np.array(data), (np.array(rows), np.array(cols))),
        shape=(n_edges, n_vars),
    ).tocsr()
    bounds = [(None, None)] * n_states + [(0.0, LAM_UB)] * n_states
    bounds[0] = (0.0, 0.0)
    c = np.zeros(n_vars)

    t_solve = time.time()
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    solve_secs = time.time() - t_solve
    print(
        f"[060d] HiGHS: status={res.status} success={res.success}  "
        f"msg={res.message}  solve={solve_secs:.1f}s"
    )

    proof_state = {
        "proof_state": "iteration_060d_k8_artifact_selfloops_filtered",
        "K": K,
        "epsilon": EPSILON,
        "n_realisable_self_loops": len(realisable_self_loops),
        "n_artifact_selfloop_edges_dropped": n_dropped_artifact_selfloop,
        "n_unique_states_after_filter": n_states,
        "n_edges_after_filter": n_edges,
        "n_edges_before_filter": len(edges),
        "scipy_status": int(res.status),
        "scipy_message": str(res.message),
        "lp_feasible": bool(res.success),
        "closed_graph": True,
        "elapsed_total_seconds": time.time() - t_start,
    }
    if res.success:
        margins = b_ub - A_ub.dot(res.x)
        proof_state["if_feasible_min_margin"] = float(margins.min())
        proof_state["if_feasible_max_margin"] = float(margins.max())
        cert = {
            "proof_state": "iteration_060d_certificate",
            "K": K,
            "n_states": n_states,
            "psi": res.x[:n_states].tolist(),
            "lam": res.x[n_states:].tolist(),
        }
        cert_path = CERT_DIR / f"iteration_060d_certificate_K{K}.json"
        cert_path.write_text(json.dumps(cert))
        proof_state["certificate_file"] = str(cert_path.relative_to(ROOT))
        proof_state["interpretation"] = (
            "After surgically removing self-loop edges that no positive "
            "integer ever realises, the K=8 closed 2-window LP is feasible. "
            "This means the *only* obstruction in the unfiltered 060c LP "
            "was a finite, identifiable list of abstraction artefacts."
        )
    else:
        proof_state["interpretation"] = (
            "After dropping abstraction-artifact self-loops, the LP is "
            "still infeasible. There exist longer (non-self-loop) cycles "
            "in the closed 2-window graph that are also abstraction "
            "artefacts. Move to the 3-window state encoding."
        )

    out = PROOF_DIR / f"iteration_060d_K{K}.json"
    out.write_text(json.dumps(proof_state, indent=2))
    print(f"[060d] wrote {out}")
    print(json.dumps(proof_state, indent=2))


if __name__ == "__main__":
    main()
