"""Iteration 060c: K=8 closed affine residue-aware LP, c_val-split.

Implements the spec from program.md:

  - States are 2-window edge states E = (r1, pi0, r2, pi1).
  - Transitions E1 -> E2 are enumerated by simulating 3 windows of K bits.
  - Drift is attached to the *middle* window (pi_middle = pi_1):
        d = popcount(pi_middle) * (1 + log2(3)) - K
  - Depth shift c_val = delta_pi2(n3) - delta_pi1(n2), where
        delta_pi(n) = v2(n - f_pi),
        f_pi = B / (2^(K-m) - 3^m).
  - LP variables: psi[i] (free), lam[i] (>= 0).
  - Anchor: psi[0] = 0.
  - Per-(E1, E2, c_val) constraint:
        psi[E2] - psi[E1] + c_val * lam[E2] <= -d - EPSILON
  - No monotonicity on lam (deliberately removed from 060a; this is the
    point of c_val splitting -- letting different fibers in the same
    (E1, E2) family carry their own depth-shift instead of collapsing to
    worst-case c_max).

Outputs:
  - proof_states/iteration_060c.json
  - certificates/iteration_060c_certificate.json (if feasible)
  - witnesses/iteration_060c_cycle.json (if infeasible)

Mathematical sanity-checks performed:
  - Boundary residues from the affine recurrence match direct simulation.
  - LOG2_3_UPPER = Fraction(1584962500721157, 10**15) is used in the exact
    rational re-verification path (when the LP is feasible).
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


# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------
K = int(os.environ.get("ITER_K", 8))
EPSILON = float(os.environ.get("ITER_EPS", 1e-2))
LAM_UB = float(os.environ.get("ITER_LAM_UB", 128.0))
EXHAUSTIVE = os.environ.get("ITER_EXHAUSTIVE", "1") == "1"
RANDOM_SAMPLES = int(os.environ.get("ITER_RANDOM_SAMPLES", 2_000_000))
RANDOM_SEED = 42

ROOT = Path(__file__).resolve().parent.parent
PROOF_DIR = ROOT / "proof_states"
CERT_DIR = ROOT / "certificates"
WITNESS_DIR = ROOT / "witnesses"
for d in (PROOF_DIR, CERT_DIR, WITNESS_DIR):
    d.mkdir(parents=True, exist_ok=True)

LOG2_3_UPPER = Fraction(1584962500721157, 10**15)
LOG2_3_FLOAT = math.log2(3.0)


# ----------------------------------------------------------------------
# Affine recurrence and direct simulation
# ----------------------------------------------------------------------
def affine_constants(r: int, k: int):
    """Compute (A, B, S, mask, n_final) for window of length k starting at r.

    Uses the user-specified recurrence in *time order*:
      A=1, B=0, S=0
      for bit in time order:
        if odd: B = 3B + 2^S; A = 3A
        if even: S += 1
    Verifies the affine identity against direct simulation.

    Returns mask in the same convention as 060a/b, which packs the first
    bit at the high end (mask = (mask << 1) | bit).
    """
    A = 1
    B = 0
    S = 0
    n = r
    mask = 0
    for _ in range(k):
        b = n & 1
        mask = (mask << 1) | b
        if b == 1:
            B = 3 * B + (1 << S)
            A = 3 * A
            n = 3 * n + 1
        else:
            S += 1
            n //= 2
    # Affine identity check (cheap; aborts on mismatch)
    if (A * r + B) != n * (1 << S):
        raise AssertionError(
            f"affine recurrence != simulation: r={r}, A={A}, B={B}, S={S}, n={n}"
        )
    return A, B, S, mask, n


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


DELTA_SAT = 64  # 2-adic-distance saturation cap (window-scale, not 10^9)


def v2_int(val: int, cap: int = DELTA_SAT) -> int:
    """2-adic valuation, capped at `cap` to keep LP coefficients bounded.

    The cap matters for `n == f_pi` (orbit hits an affine fixed point exactly,
    e.g. the trivial 1->4->2->1 cycle). At that point v2(n - f_pi) = +infinity;
    we represent it by `cap` so it does not blow up the LP coefficient or the
    Bellman-Ford weights.
    """
    if val == 0:
        return cap
    val = abs(val)
    raw = (val & -val).bit_length() - 1
    return raw if raw < cap else cap


def delta_pi(n: int, B: int, denom: int) -> int:
    """delta_pi(n) = v2(n - f_pi) where f_pi = B / denom (with our sign
    convention B = 2^(K-m)*f_pi - 3^m*r, denom = 2^(K-m) - 3^m, denom odd).

    Computes v2(n*denom - B) which equals v2(n - f_pi) up to the v2(denom) = 0
    factor.
    """
    return v2_int(n * denom - B)


# ----------------------------------------------------------------------
# Stage 1: precompute per-residue affine constants
# ----------------------------------------------------------------------
def precompute_residue_table(k: int):
    n_res = 1 << k
    info = []  # index = r, value = (B, denom, mask, A, n_final, m)
    mask_to_r = {}
    for r in range(n_res):
        A, B, S, mask, n_final = affine_constants(r, k)
        m = k - S
        denom = (1 << S) - A  # = 2^(K-m) - 3^m
        info.append((B, denom, mask, A, n_final, m))
        mask_to_r[mask] = r
    return info, mask_to_r


# ----------------------------------------------------------------------
# Stage 2: enumerate fibers, build c_val-split multigraph
# ----------------------------------------------------------------------
def enumerate_edges(k: int, exhaustive: bool, samples: int):
    n_res = 1 << k
    n_fibers = 1 << (3 * k)
    info, mask_to_r = precompute_residue_table(k)

    # multigraph keyed by (E1, E2, c_val); value records canonical witness.
    edges = {}

    if exhaustive:
        seeds = range(1, n_fibers)  # skip 0 (degenerate)
    else:
        rng = np.random.default_rng(RANDOM_SEED)
        seeds = rng.integers(1, 1 << (3 * k + 8), size=samples).tolist()

    t0 = time.time()
    progress_step = max(1, len(seeds) // 20) if hasattr(seeds, "__len__") else 1_000_000
    count = 0

    for n0 in seeds:
        n_sim = int(n0)

        # Window 0 -> r1
        m0, n1, pi_0 = simulate_window(n_sim, k)
        r1 = n1 & (n_res - 1)

        # Window 1 -> r2; pi_1 will be the middle window for the next transition
        m1, n2, pi_1 = simulate_window(n1, k)
        r2 = n2 & (n_res - 1)
        B1, den1, _, _, _, _ = info[mask_to_r[pi_1]]
        delta_1 = delta_pi(n2, B1, den1)

        E1 = (r1, pi_0, r2, pi_1)

        # Window 2 -> r3
        m2, n3, pi_2 = simulate_window(n2, k)
        r3 = n3 & (n_res - 1)
        B2, den2, _, _, _, _ = info[mask_to_r[pi_2]]
        delta_2 = delta_pi(n3, B2, den2)

        E2 = (r2, pi_1, r3, pi_2)

        # Drift attaches to pi_middle = pi_1 (per spec)
        m_middle = m1
        c_val = delta_2 - delta_1

        key = (E1, E2, c_val)
        if key not in edges:
            edges[key] = {
                "drift_float": m_middle * (1.0 + LOG2_3_FLOAT) - k,
                "m_middle": m_middle,
                "pi_middle": pi_1,
                "n_example": n_sim,
                "n2_example": n2,
                "n3_example": n3,
                "delta_1_example": delta_1,
                "delta_2_example": delta_2,
                "count": 0,
            }
        edges[key]["count"] += 1

        count += 1
        if count % progress_step == 0:
            elapsed = time.time() - t0
            print(
                f"  enumerated {count:>10}/{len(seeds) if hasattr(seeds, '__len__') else '?'} "
                f"fibers in {elapsed:6.1f}s, edges={len(edges):,}",
                flush=True,
            )

    return edges, info, mask_to_r


# ----------------------------------------------------------------------
# Stage 3: build LP
# ----------------------------------------------------------------------
def build_lp(edges):
    state_set = set()
    for (E1, E2, _) in edges:
        state_set.add(E1)
        state_set.add(E2)
    states = sorted(state_set)
    state_to_idx = {s: i for i, s in enumerate(states)}
    n_states = len(states)
    n_edges = len(edges)

    # Variables: x = [psi_0, ..., psi_{N-1}, lam_0, ..., lam_{N-1}]
    n_vars = 2 * n_states

    rows = []
    cols = []
    data = []
    b_ub = np.zeros(n_edges, dtype=np.float64)

    edge_list = list(edges.items())  # list of ((E1,E2,c), info_dict)

    for i, ((E1, E2, c_val), inf) in enumerate(edge_list):
        i1 = state_to_idx[E1]
        i2 = state_to_idx[E2]
        rows.append(i); cols.append(i2); data.append(1.0)
        rows.append(i); cols.append(i1); data.append(-1.0)
        rows.append(i); cols.append(n_states + i2); data.append(float(c_val))
        b_ub[i] = -inf["drift_float"] - EPSILON

    A_ub = coo_matrix(
        (np.array(data, dtype=np.float64),
         (np.array(rows, dtype=np.int64), np.array(cols, dtype=np.int64))),
        shape=(n_edges, n_vars),
    ).tocsr()

    # Bounds: psi free, lam in [0, LAM_UB]; psi[0] anchored to 0.
    bounds = [(None, None)] * n_states + [(0.0, LAM_UB)] * n_states
    bounds[0] = (0.0, 0.0)  # psi[0] = 0 anchor

    c = np.zeros(n_vars, dtype=np.float64)  # screening LP, zero objective

    return {
        "A_ub": A_ub,
        "b_ub": b_ub,
        "c": c,
        "bounds": bounds,
        "edge_list": edge_list,
        "states": states,
        "state_to_idx": state_to_idx,
        "n_states": n_states,
        "n_edges": n_edges,
        "n_vars": n_vars,
    }


def solve_lp(lp):
    res = linprog(
        lp["c"],
        A_ub=lp["A_ub"],
        b_ub=lp["b_ub"],
        bounds=lp["bounds"],
        method="highs",
    )
    return res


# ----------------------------------------------------------------------
# Stage 4: cycle witness extraction (Bellman-Ford on a depth-free abstraction)
# ----------------------------------------------------------------------
def extract_cycle_witness(lp, edges):
    """Extract a closed cycle in the c_val-split graph via Bellman-Ford.

    Two abstractions are tried in order:
      (A) lam=0 (depth-free): edge weight w_e = -d_e - EPSILON.
          A negative cycle here proves Σ d_e > -|cyc|*EPSILON > 0,
          which is infeasible regardless of any lam choice.
      (B) lam=LAM_UB and per-(E1,E2) take MIN c_val (lam-friendliest):
          weight w_e = -d_e - LAM_UB * c_val_min - EPSILON.
          A negative cycle here means even the lam-friendliest assignment
          cannot satisfy the constraints -- but the witness depends on lam.

    For each cycle the witness records:
      cycle_total_drift, cycle_total_depth_effect (sum of c_val), and
      whether the concatenated parity mask is realised by a single integer.
    """
    state_to_idx = lp["state_to_idx"]
    states = lp["states"]
    n_states = lp["n_states"]

    # Reduce parallel edges per (E1, E2): keep min c_val and max c_val records.
    edge_min = {}
    edge_max = {}
    for (E1, E2, c_val), info in edges.items():
        i1 = state_to_idx[E1]
        i2 = state_to_idx[E2]
        key = (i1, i2)
        d = info["drift_float"]
        if key not in edge_min or c_val < edge_min[key]["c_val"]:
            edge_min[key] = {"c_val": c_val, "drift": d, "info": info, "E1": E1, "E2": E2}
        if key not in edge_max or c_val > edge_max[key]["c_val"]:
            edge_max[key] = {"c_val": c_val, "drift": d, "info": info, "E1": E1, "E2": E2}

    BF_MAX_ITERS = int(os.environ.get("ITER_BF_MAX_ITERS", 200))

    def bf(weights_per_edge):
        """Bounded Bellman-Ford. Caps at BF_MAX_ITERS (default 200, per 060b).

        weights_per_edge: dict (i1, i2) -> (w, info_dict).
        Returns list of (i1, i2, info_pkg) along a closed cycle, or None.
        """
        edges_arr = list(weights_per_edge.items())
        m = len(edges_arr)
        s1 = np.zeros(m, dtype=np.int64)
        s2 = np.zeros(m, dtype=np.int64)
        w = np.zeros(m, dtype=np.float64)
        for k_, ((i1, i2), (ww, _)) in enumerate(edges_arr):
            s1[k_] = i1
            s2[k_] = i2
            w[k_] = ww

        dist = np.zeros(n_states, dtype=np.float64)
        pred_node = np.full(n_states, -1, dtype=np.int64)
        pred_edge = np.full(n_states, -1, dtype=np.int64)

        last_relaxed = -1
        budget = min(BF_MAX_ITERS, n_states)
        for it in range(budget):
            cand = dist[s1] + w
            improved = cand < dist[s2] - 1e-12
            if not np.any(improved):
                return None
            imp_idx = np.where(improved)[0]
            dist[s2[imp_idx]] = cand[imp_idx]
            pred_node[s2[imp_idx]] = s1[imp_idx]
            pred_edge[s2[imp_idx]] = imp_idx
            if it == budget - 1:
                last_relaxed = int(s2[imp_idx[0]])

        if last_relaxed == -1:
            return None

        # Walk back to land inside the cycle.
        v = last_relaxed
        for _ in range(budget):
            v = int(pred_node[v])
            if v == -1:
                return None

        cycle_start = v
        path = []
        cur = cycle_start
        for _ in range(budget + 5):
            e_idx = int(pred_edge[cur])
            if e_idx < 0:
                return None
            (i1, i2), (_, info_pkg) = edges_arr[e_idx]
            path.append((i1, i2, info_pkg))
            cur = int(pred_node[cur])
            if cur == cycle_start:
                path.reverse()
                return path
            if cur == -1:
                return None
        return None

    # Abstraction A: depth-free
    weights_A = {
        k: (-v["drift"] - EPSILON, v) for k, v in edge_max.items()  # any parallel edge works for drift
    }
    cycle_A = bf(weights_A)

    # Abstraction B: lam-friendliest (use min c_val for each pair)
    weights_B = {
        k: (-v["drift"] - LAM_UB * v["c_val"] - EPSILON, v) for k, v in edge_min.items()
    }
    cycle_B = bf(weights_B)

    return {
        "depth_free_cycle": cycle_A,
        "lam_friendliest_cycle": cycle_B,
        "edge_min": edge_min,
        "edge_max": edge_max,
    }


# ----------------------------------------------------------------------
# Stage 5: integer realisability of a concatenated parity-mask cycle
# ----------------------------------------------------------------------
def cycle_integer_realisable(cycle_path, k: int):
    """Given a list of (E1, E2, info) edges, build the concatenated parity
    mask (each edge contributes pi_middle of length k bits) and try to
    solve for the unique fixed point of the affine map.

    Returns (realisable: bool, n_value: int|None, denom: int, num: int).
    """
    if not cycle_path:
        return (False, None, 0, 0)

    # Concatenate pi_middle bits in order. Bits inside each pi_middle are
    # already in time order in the integer encoding (`mask = (mask << 1) | bit`),
    # so the highest bit of pi_middle is the FIRST step. We need to feed bits
    # into the recurrence in time order.
    bits_time_order = []
    for (_, _, info) in cycle_path:
        pi = info["pi_middle"]
        # pi has top bit = first step
        for j in range(k - 1, -1, -1):
            bits_time_order.append((pi >> j) & 1)

    A = 1
    B = 0
    S = 0
    for b in bits_time_order:
        if b == 1:
            B = 3 * B + (1 << S)
            A = 3 * A
        else:
            S += 1
    # Cycle realisability: T(n) = (A n + B)/2^S = n => n*(2^S - A) = B
    denom = (1 << S) - A
    if denom == 0:
        return (False, None, denom, B)
    if B % denom != 0:
        return (False, None, denom, B)
    n_val = B // denom
    if n_val <= 0:
        return (False, n_val, denom, B)
    return (True, n_val, denom, B)


# ----------------------------------------------------------------------
# Stage 6: exact rational verifier (used when LP is feasible)
# ----------------------------------------------------------------------
def exact_rational_verify(lp, res, edges, k: int):
    """Re-verify each constraint using LOG2_3_UPPER = Fraction(...) instead
    of float log2(3). Returns (all_pass, max_violation_fraction).

    Constraint:  psi[E2] - psi[E1] + c_val * lam[E2] <= -(m_middle*(1+log2_3) - K) - eps
    Rationally:  psi[E2] - psi[E1] + c_val * lam[E2] + m_middle*(1+LOG2_3_UPPER) - K + eps <= 0
    """
    psi = res.x[: lp["n_states"]]
    lam = res.x[lp["n_states"]:]

    # Convert solution to rationals via limit_denominator for tractability.
    psi_q = [Fraction(float(p)).limit_denominator(10**12) for p in psi]
    lam_q = [Fraction(float(l)).limit_denominator(10**12) for l in lam]
    eps_q = Fraction(EPSILON).limit_denominator(10**12)
    one_plus_log2_3 = Fraction(1) + LOG2_3_UPPER

    max_viol = Fraction(0)
    n_fail = 0
    for (E1, E2, c_val), info in edges.items():
        i1 = lp["state_to_idx"][E1]
        i2 = lp["state_to_idx"][E2]
        m_mid = info["m_middle"]
        # Required: psi[i2] - psi[i1] + c_val*lam[i2] + m_mid*(1+LOG2_3_UPPER) - K + eps_q <= 0
        lhs = (
            psi_q[i2] - psi_q[i1]
            + Fraction(int(c_val)) * lam_q[i2]
            + Fraction(m_mid) * one_plus_log2_3
            - Fraction(k)
            + eps_q
        )
        if lhs > 0:
            n_fail += 1
            if lhs > max_viol:
                max_viol = lhs

    return n_fail == 0, str(max_viol), n_fail


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    overall_t0 = time.time()
    print(
        f"[060c] starting K={K} epsilon={EPSILON} lam_ub={LAM_UB} "
        f"exhaustive={EXHAUSTIVE} samples={RANDOM_SAMPLES}"
    )

    # ---- 1. Enumerate edges
    t0 = time.time()
    edges, info, mask_to_r = enumerate_edges(K, EXHAUSTIVE, RANDOM_SAMPLES)
    enum_secs = time.time() - t0
    print(
        f"[060c] enumeration: {len(edges):,} (E1,E2,c_val) edges in {enum_secs:.1f}s"
    )

    # Direct-simulation sanity for boundary residues:
    # already enforced inside affine_constants() via the assert.

    # ---- 2. Build LP
    t0 = time.time()
    lp = build_lp(edges)
    build_secs = time.time() - t0
    print(
        f"[060c] LP: n_states={lp['n_states']:,}  n_edges={lp['n_edges']:,}  "
        f"build={build_secs:.1f}s"
    )

    # ---- 3. Solve
    t0 = time.time()
    res = solve_lp(lp)
    solve_secs = time.time() - t0
    print(
        f"[060c] HiGHS: status={res.status} success={res.success}  "
        f"msg={res.message}  solve={solve_secs:.1f}s"
    )

    proof_state = {
        "proof_state": "iteration_060c_k8_cval_split_affine_lp",
        "K": K,
        "epsilon": EPSILON,
        "lam_upper_bound": LAM_UB,
        "log2_3_upper_rational": [
            LOG2_3_UPPER.numerator, LOG2_3_UPPER.denominator
        ],
        "exhaustive": EXHAUSTIVE,
        "random_samples": (None if EXHAUSTIVE else RANDOM_SAMPLES),
        "fibers_processed": (1 << (3 * K)) - 1 if EXHAUSTIVE else RANDOM_SAMPLES,
        "n_unique_states": lp["n_states"],
        "n_unique_cval_split_edges": lp["n_edges"],
        "n_unique_e1_e2_pairs": len({(e1, e2) for (e1, e2, _) in edges}),
        "scipy_status": int(res.status),
        "scipy_message": str(res.message),
        "lp_feasible": bool(res.success),
        "closed_graph": True,
        "drift_assignment": "pi_middle = pi_1 (between E1 and E2)",
        "monotonicity_constraint_on_lambda": False,
        "differs_from_060a_b_in": [
            "drift uses pi_middle=pi_1, not pi_2",
            "edges grouped by (E1,E2,c_val) instead of (E1,E2)+max(c_val)",
            "no monotonicity constraint on lambda",
        ],
        "elapsed_enum_seconds": enum_secs,
        "elapsed_lp_build_seconds": build_secs,
        "elapsed_lp_solve_seconds": solve_secs,
    }

    if res.success:
        margins = lp["b_ub"] - lp["A_ub"].dot(res.x)
        proof_state["if_feasible_min_margin"] = float(margins.min())
        proof_state["if_feasible_max_margin"] = float(margins.max())

        # Export certificate
        cert = {
            "proof_state": "iteration_060c_certificate",
            "K": K,
            "n_states": lp["n_states"],
            "psi": res.x[: lp["n_states"]].tolist(),
            "lam": res.x[lp["n_states"]:].tolist(),
            "states_repr": [
                {"r1": s[0], "pi0": s[1], "r2": s[2], "pi1": s[3]}
                for s in lp["states"]
            ],
        }
        cert_path = CERT_DIR / f"iteration_060c_certificate_K{K}.json"
        cert_path.write_text(json.dumps(cert))
        proof_state["certificate_file"] = str(cert_path.relative_to(ROOT))

        # Exact rational re-verification
        t0 = time.time()
        ok, max_viol, n_fail = exact_rational_verify(lp, res, edges, K)
        proof_state["exact_rational_verified"] = bool(ok)
        proof_state["exact_rational_max_violation"] = max_viol
        proof_state["exact_rational_failed_constraints"] = int(n_fail)
        proof_state["elapsed_exact_verify_seconds"] = time.time() - t0

    else:
        proof_state["witness_extracted"] = False
        # Witness extraction
        wit = extract_cycle_witness(lp, edges)

        def package_cycle(cycle_path, label):
            if cycle_path is None:
                return None
            tot_drift = 0.0
            tot_dep = 0
            cycle_json = []
            for (i1, i2, infopkg) in cycle_path:
                E1 = infopkg["E1"]
                E2 = infopkg["E2"]
                drift = infopkg["drift"]
                c_val = infopkg["c_val"]
                tot_drift += drift
                tot_dep += int(c_val)
                inner = infopkg["info"]
                cycle_json.append({
                    "E1": f"(r1={E1[0]}, pi0={E1[1]:0{K}b}, r2={E1[2]}, pi1={E1[3]:0{K}b})",
                    "E2": f"(r2={E2[0]}, pi1={E2[1]:0{K}b}, r3={E2[2]}, pi2={E2[3]:0{K}b})",
                    "pi_middle": f"{inner['pi_middle']:0{K}b}",
                    "m_middle": int(inner["m_middle"]),
                    "drift_float": float(drift),
                    "c_val": int(c_val),
                    "n_example": int(inner["n_example"]),
                    "n2_example": int(inner["n2_example"]),
                    "n3_example": int(inner["n3_example"]),
                    "delta_1_example": int(inner["delta_1_example"]),
                    "delta_2_example": int(inner["delta_2_example"]),
                    "fiber_count": int(inner["count"]),
                })
            cycle_path_for_realiser = [
                (cyc[0], cyc[1], cyc[2]["info"]) for cyc in cycle_path
            ]
            realised, n_val, denom, num = cycle_integer_realisable(
                cycle_path_for_realiser, K
            )
            return {
                "label": label,
                "cycle_length": len(cycle_json),
                "cycle_total_drift": float(tot_drift),
                "cycle_total_depth_effect": int(tot_dep),
                "integer_realizable_single_orbit": bool(realised),
                "realised_n_value": (None if n_val is None else int(n_val)),
                "realised_denom": int(denom),
                "realised_num": int(num),
                "cycle_edges": cycle_json,
            }

        depth_free = package_cycle(wit["depth_free_cycle"], "depth_free_lam0")
        lam_friend = package_cycle(wit["lam_friendliest_cycle"], "lam_friendliest_min_cval")

        witness_payload = {
            "K": K,
            "iteration": "060c",
            "depth_free_witness": depth_free,
            "lam_friendliest_witness": lam_friend,
            "interpretation": (
                "If depth_free_witness is non-null with positive total drift, "
                "the LP is infeasible regardless of any depth-Lyapunov choice "
                "(real obstruction at the K=8 closed-affine-graph level). "
                "If only the lam_friendliest_witness is non-null, the obstruction "
                "depends on the depth weighting; this is a stitching/abstraction "
                "artifact of the 2-window state encoding and we should expand to "
                "3-window states (Iteration 061)."
            ),
        }
        wit_path = WITNESS_DIR / f"iteration_060c_cycle_K{K}.json"
        wit_path.write_text(json.dumps(witness_payload, indent=2))
        proof_state["witness_file"] = str(wit_path.relative_to(ROOT))
        proof_state["witness_extracted"] = depth_free is not None or lam_friend is not None
        proof_state["depth_free_obstruction_detected"] = depth_free is not None
        if depth_free is not None:
            proof_state["depth_free_cycle_total_drift"] = depth_free["cycle_total_drift"]
            proof_state["depth_free_cycle_length"] = depth_free["cycle_length"]
            proof_state["depth_free_cycle_integer_realizable_single_orbit"] = (
                depth_free["integer_realizable_single_orbit"]
            )
        if lam_friend is not None:
            proof_state["lam_friendliest_cycle_total_drift"] = lam_friend["cycle_total_drift"]
            proof_state["lam_friendliest_cycle_total_depth_effect"] = lam_friend["cycle_total_depth_effect"]
            proof_state["lam_friendliest_cycle_length"] = lam_friend["cycle_length"]
            proof_state["lam_friendliest_cycle_integer_realizable_single_orbit"] = (
                lam_friend["integer_realizable_single_orbit"]
            )

        if depth_free is not None:
            proof_state["obstruction_class"] = "real_drift_only_cycle_lp_infeasible_for_any_lambda"
        elif lam_friend is not None:
            proof_state["obstruction_class"] = "lambda_dependent_likely_2window_abstraction_artifact"
        else:
            proof_state["obstruction_class"] = "no_negative_cycle_found_LP_disagreement_or_solver_artifact"
            proof_state["unexplained_failures"] = 1

    proof_state["total_elapsed_seconds"] = time.time() - overall_t0

    out = PROOF_DIR / f"iteration_060c_K{K}.json"
    out.write_text(json.dumps(proof_state, indent=2))
    print(f"[060c] wrote {out}")
    print(json.dumps(
        {k: v for k, v in proof_state.items() if k != "states_repr"}, indent=2
    ))


if __name__ == "__main__":
    main()
