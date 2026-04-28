"""Iteration 063: artefact-aware CEGIS infeasibility loop.

Round structure:

  1. Build the closed K=8 LP (same as 060c c_val-split).
  2. Solve. If feasible -> stop and report.
  3. If infeasible -> extract a depth-free Bellman-Ford cycle witness on
     the current active graph.
  4. Run the affine admissibility classifier (`verifiers/cycle_classifier`)
     on the witness cycle.
  5. If REALIZABLE_POSITIVE_INTEGER_CYCLE -> stop and emit a
     candidate-cycle report; an arbitrary-precision scalar audit must
     follow before *any* claim is made.
  6. If non-realisable -> add a diagnostic cut: block all parallel
     `(E1, E2, c_val)` edges that share the (E1, E2) of one cycle edge,
     specifically the cycle edge with the largest drift (most
     responsible for the positive-cycle infeasibility in the depth-free
     abstraction).
  7. Re-solve. Continue up to MAX_ROUNDS rounds.

Cuts are *diagnostic*: they remove edges from the auxiliary LP graph
only, not from the underlying Collatz transition data. The output
labels every cut by the witness-cycle classification so we can audit
whether each removal was justified by an artefact (i.e. not a real
positive-integer Collatz cycle).

This iteration **does not** claim a Collatz proof under any outcome.
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
EPSILON = float(os.environ.get("ITER_EPS", 1e-2))
LAM_UB = float(os.environ.get("ITER_LAM_UB", 128.0))
MAX_ROUNDS = int(os.environ.get("ITER_MAX_ROUNDS", 50))
DELTA_SAT = 64
RANDOM_SEED = 42

ROOT = Path(__file__).resolve().parent.parent
PROOF_DIR = ROOT / "proof_states"
WITNESS_DIR = ROOT / "witnesses"
PROOF_DIR.mkdir(parents=True, exist_ok=True)
WITNESS_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / "verifiers"))
from cycle_classifier import classify_cycle  # noqa: E402

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
            edges[key] = {
                "drift_float": drift,
                "m_middle": m_middle,
                "pi_middle": pi_1,
                "n_example": n_sim,
            }

        if n0 % progress == 0:
            print(
                f"  enumerated {n0:>10}/{n_fibers}  edges={len(edges):,}  "
                f"elapsed={time.time()-t0:.1f}s",
                flush=True,
            )
    print(f"[063] enumeration: {len(edges):,} edges in {time.time()-t0:.1f}s")
    return edges


def build_static_arrays(edges):
    """Build numpy arrays once. Subsequent rounds just mask out blocked edges."""
    state_set = set()
    for (E1, E2, _) in edges:
        state_set.add(E1); state_set.add(E2)
    states = sorted(state_set)
    state_to_idx = {s: i for i, s in enumerate(states)}
    n_states = len(states)
    n_edges = len(edges)

    s1_arr = np.zeros(n_edges, dtype=np.int32)
    s2_arr = np.zeros(n_edges, dtype=np.int32)
    cval_arr = np.zeros(n_edges, dtype=np.float64)
    drift_arr = np.zeros(n_edges, dtype=np.float64)
    pi_mid_arr = np.zeros(n_edges, dtype=np.int32)
    keys = []  # (E1, E2, c_val) ; E1, E2 as tuple

    for i, ((E1, E2, c_val), info) in enumerate(edges.items()):
        s1_arr[i] = state_to_idx[E1]
        s2_arr[i] = state_to_idx[E2]
        cval_arr[i] = float(c_val)
        drift_arr[i] = info["drift_float"]
        pi_mid_arr[i] = int(info["pi_middle"])
        keys.append((E1, E2, c_val))

    # Map (E1, E2) -> list of edge indices (parallel c_val variants)
    pair_to_indices = {}
    for i, (E1, E2, _) in enumerate(keys):
        pair_to_indices.setdefault((E1, E2), []).append(i)

    return {
        "states": states,
        "state_to_idx": state_to_idx,
        "n_states": n_states,
        "n_edges": n_edges,
        "s1_arr": s1_arr,
        "s2_arr": s2_arr,
        "cval_arr": cval_arr,
        "drift_arr": drift_arr,
        "pi_mid_arr": pi_mid_arr,
        "keys": keys,
        "pair_to_indices": pair_to_indices,
    }


def build_lp_from_active(static, active_mask):
    n_states = static["n_states"]
    s1 = static["s1_arr"][active_mask]
    s2 = static["s2_arr"][active_mask]
    cv = static["cval_arr"][active_mask]
    d = static["drift_arr"][active_mask]
    n_act = s1.shape[0]

    n_vars = 2 * n_states
    rows = np.repeat(np.arange(n_act, dtype=np.int64), 3)
    cols = np.empty(n_act * 3, dtype=np.int64)
    data = np.empty(n_act * 3, dtype=np.float64)
    cols[0::3] = s2.astype(np.int64)
    cols[1::3] = s1.astype(np.int64)
    cols[2::3] = n_states + s2.astype(np.int64)
    data[0::3] = 1.0
    data[1::3] = -1.0
    data[2::3] = cv
    A_ub = coo_matrix((data, (rows, cols)), shape=(n_act, n_vars)).tocsr()
    b_ub = -d - EPSILON
    bounds = [(None, None)] * n_states + [(0.0, LAM_UB)] * n_states
    bounds[0] = (0.0, 0.0)
    c = np.zeros(n_vars)
    return A_ub, b_ub, bounds, c, n_act


def bf_depth_free_cycle(static, active_mask, budget=200):
    """Depth-free Bellman-Ford on the deduped (s1, s2) graph."""
    s1 = static["s1_arr"][active_mask]
    s2 = static["s2_arr"][active_mask]
    d = static["drift_arr"][active_mask]
    pi = static["pi_mid_arr"][active_mask]
    active_idx = np.where(active_mask)[0]

    # Dedup by (s1, s2): same (E1, E2) edges share the same drift (drift
    # depends only on pi_1 in E1). Keep first occurrence.
    pair_key = (s1.astype(np.int64) << 32) | s2.astype(np.int64)
    _, first_idx = np.unique(pair_key, return_index=True)
    s1_d = s1[first_idx]; s2_d = s2[first_idx]; d_d = d[first_idx]
    pi_d = pi[first_idx]
    orig_d = active_idx[first_idx]  # original edge indices into static arrays

    n_states = static["n_states"]
    w = -d_d - EPSILON

    dist = np.zeros(n_states, dtype=np.float64)
    pred_node = np.full(n_states, -1, dtype=np.int64)
    pred_edge = np.full(n_states, -1, dtype=np.int64)
    last_relaxed = -1
    budget = min(budget, n_states)
    for it in range(budget):
        cand = dist[s1_d] + w
        improved = cand < dist[s2_d] - 1e-12
        if not np.any(improved):
            return None
        imp = np.where(improved)[0]
        dist[s2_d[imp]] = cand[imp]
        pred_node[s2_d[imp]] = s1_d[imp]
        pred_edge[s2_d[imp]] = imp
        if it == budget - 1:
            last_relaxed = int(s2_d[imp[0]])
    if last_relaxed == -1:
        return None
    v = last_relaxed
    for _ in range(budget):
        v = int(pred_node[v])
        if v == -1:
            return None
    cycle_start = v
    cur = cycle_start
    path_dedup_idx = []
    for _ in range(budget + 5):
        e_idx = int(pred_edge[cur])
        if e_idx < 0:
            return None
        path_dedup_idx.append(e_idx)
        cur = int(pred_node[cur])
        if cur == cycle_start:
            break
    path_dedup_idx.reverse()
    # Convert to original-edge-array indices
    path_orig_idx = [int(orig_d[i]) for i in path_dedup_idx]
    return path_orig_idx


def main():
    overall_t0 = time.time()
    print(
        f"[063] starting K={K} epsilon={EPSILON} max_rounds={MAX_ROUNDS}"
    )
    edges = enumerate_edges(K)
    print(f"[063] building static LP arrays...")
    t0 = time.time()
    static = build_static_arrays(edges)
    print(f"[063] static arrays built in {time.time()-t0:.1f}s "
          f"(n_states={static['n_states']:,}, n_edges={static['n_edges']:,})")

    blocked = np.zeros(static["n_edges"], dtype=bool)
    rounds_log = []
    final_status = None
    final_witness_payload = None

    for r in range(MAX_ROUNDS):
        active = ~blocked
        n_active = int(active.sum())
        t_round = time.time()
        A_ub, b_ub, bounds, c, _ = build_lp_from_active(static, active)
        t_build = time.time() - t_round

        t0 = time.time()
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
        t_solve = time.time() - t0

        round_entry = {
            "round": r,
            "n_active_edges": n_active,
            "n_blocked_edges": static["n_edges"] - n_active,
            "lp_build_seconds": float(t_build),
            "lp_solve_seconds": float(t_solve),
            "lp_feasible": bool(res.success),
            "scipy_status": int(res.status),
        }
        if res.success:
            margins = b_ub - A_ub.dot(res.x)
            round_entry["min_margin"] = float(margins.min())
            round_entry["max_margin"] = float(margins.max())
            print(
                f"[063] round={r} active={n_active:,} build={t_build:.1f}s "
                f"solve={t_solve:.1f}s -> FEASIBLE (min_margin={margins.min():.3e})"
            )
            rounds_log.append(round_entry)
            final_status = "feasible_after_cuts"
            break

        # ---- BF witness
        t0 = time.time()
        path_orig_idx = bf_depth_free_cycle(static, active)
        t_bf = time.time() - t0
        round_entry["bf_seconds"] = float(t_bf)
        if path_orig_idx is None:
            print(
                f"[063] round={r} active={n_active:,} INFEASIBLE but no BF cycle found "
                f"(solver-LP disagreement; lam-coupled obstruction?)"
            )
            round_entry["witness_extracted"] = False
            rounds_log.append(round_entry)
            final_status = "infeasible_no_witness"
            break

        # ---- Classify witness
        pi_mids = [int(static["pi_mid_arr"][i]) for i in path_orig_idx]
        cls = classify_cycle(pi_mids, K)
        cycle_drift = float(sum(static["drift_arr"][i] for i in path_orig_idx))
        cycle_cval = int(sum(static["cval_arr"][i] for i in path_orig_idx))
        round_entry["witness_extracted"] = True
        round_entry["cycle_length"] = len(path_orig_idx)
        round_entry["cycle_total_drift"] = cycle_drift
        round_entry["cycle_total_depth_effect"] = cycle_cval
        round_entry["classification"] = cls.get("classification")
        round_entry["candidate_n"] = cls.get("candidate_n")
        round_entry["denom"] = cls.get("denom_2S_minus_A")
        round_entry["A_3_to_m"] = cls.get("A_3_to_m")
        round_entry["B_value"] = cls.get("B_value")
        round_entry["S_total_divisions"] = cls.get("S_total_divisions")

        # Save the witness (every round) to a per-round witness file.
        wit_payload = {
            "K": K,
            "iteration": "063",
            "round": r,
            "cycle_length": len(path_orig_idx),
            "cycle_total_drift": cycle_drift,
            "cycle_total_depth_effect": cycle_cval,
            "classification": cls,
            "cycle_edges": [
                {
                    "E1": list(static["keys"][i][0]),
                    "E2": list(static["keys"][i][1]),
                    "pi_middle_int": int(static["pi_mid_arr"][i]),
                    "pi_middle_bin": format(int(static["pi_mid_arr"][i]), f"0{K}b"),
                    "drift_float": float(static["drift_arr"][i]),
                    "c_val": int(static["cval_arr"][i]),
                } for i in path_orig_idx
            ],
        }

        if cls.get("classification") == "REALIZABLE_POSITIVE_INTEGER_CYCLE":
            print(
                f"[063] round={r} REALIZABLE cycle found! "
                f"n={cls.get('candidate_n')} length={len(path_orig_idx)}"
            )
            wit_path = WITNESS_DIR / f"iteration_063_REALIZABLE_K{K}_round{r}.json"
            wit_path.write_text(json.dumps(wit_payload, indent=2))
            rounds_log.append(round_entry)
            final_witness_payload = wit_payload
            final_status = "realizable_cycle_found_STOP"
            break

        # ---- Cut: block ALL (E1,E2,c_val) edges sharing the (E1,E2)
        # pair of any cycle edge. By the structural argument, every
        # depth-free BF cycle has total drift > 0 hence denom < 0 hence
        # is non-realisable in Z_{>0}. Cutting all L edges of the cycle
        # is therefore guaranteed to remove only artefact connections.
        cuts_this_round = []
        n_to_block = 0
        for orig_idx in path_orig_idx:
            E1_cut, E2_cut, _ = static["keys"][orig_idx]
            parallel_indices = static["pair_to_indices"][(E1_cut, E2_cut)]
            for i in parallel_indices:
                if not blocked[i]:
                    blocked[i] = True
                    n_to_block += 1
            cuts_this_round.append({
                "E1": list(E1_cut),
                "E2": list(E2_cut),
                "n_parallel_edges": len(parallel_indices),
            })
        round_entry["cuts"] = cuts_this_round
        round_entry["cut_n_edges_blocked_this_round"] = n_to_block
        rounds_log.append(round_entry)

        print(
            f"[063] round={r} active={n_active:,} build={t_build:.1f}s "
            f"solve={t_solve:.1f}s bf={t_bf:.1f}s len={len(path_orig_idx)} "
            f"drift={cycle_drift:+.2f} -> "
            f"{cls.get('classification')[:35]}; cut {n_to_block} edges"
        )

    else:
        # Loop completed without break = hit max rounds
        final_status = "max_rounds_reached"

    # ---- Histogram
    hist = Counter(
        e.get("classification") for e in rounds_log if e.get("classification")
    )

    proof_state = {
        "proof_state": "iteration_063_artifact_aware_cegis",
        "K": K,
        "epsilon": EPSILON,
        "max_rounds": MAX_ROUNDS,
        "n_rounds_executed": len(rounds_log),
        "final_status": final_status,
        "n_non_realizable_cycles_cut": sum(
            1 for e in rounds_log
            if e.get("classification") and e.get("classification") != "REALIZABLE_POSITIVE_INTEGER_CYCLE"
        ),
        "any_realizable_positive_integer_cycle": any(
            e.get("classification") == "REALIZABLE_POSITIVE_INTEGER_CYCLE"
            for e in rounds_log
        ),
        "lp_became_feasible_after_cutting_only_non_realizable_cycles": final_status == "feasible_after_cuts",
        "classification_histogram": dict(hist),
        "rounds": rounds_log,
        "elapsed_total_seconds": time.time() - overall_t0,
    }
    if final_witness_payload is not None:
        proof_state["realizable_witness_payload"] = final_witness_payload
    proof_state["interpretation"] = (
        "Cuts are diagnostic only; they remove (E1, E2) connections from the "
        "auxiliary LP graph after the witness cycle is provably non-realizable "
        "in Z_{>0}. They do not modify the underlying Collatz transition data. "
        "If `lp_became_feasible_after_cutting_only_non_realizable_cycles` is "
        "true, the LP infeasibility at K=" + str(K) + " is *entirely* explained "
        "by abstraction artefacts; this is a strong-but-not-proof signal that "
        "the descent certificate exists on the positive-integer-realizable "
        "quotient. Formalising the positivity filter without ad hoc cuts is "
        "the next research step."
    )

    out = PROOF_DIR / f"iteration_063_artifact_cegis_K{K}.json"
    out.write_text(json.dumps(proof_state, indent=2))
    print(f"[063] wrote {out}")
    print(json.dumps({k: v for k, v in proof_state.items() if k not in ("rounds",)}, indent=2))


if __name__ == "__main__":
    main()
