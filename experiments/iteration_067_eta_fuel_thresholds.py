"""Iteration 067: eta-fuel Lyapunov prototype.

For each artefact cycle in the corpus, ask:

  Phi(n) := log_2(n) + lambda * eta(n)

is a candidate Lyapunov on positive-integer trajectories that shadow
the (negative-domain) artefact. Around one full period of the cycle:

  Delta log_2(n) = drift = m*(1 + log_2 3) - T   (exact via LOG2_3_UPPER)
  Delta eta      = -S                            (v_2-fuel lemma 066)

So  Delta Phi = drift - lambda * S.

Cycle is contractive (under shadowing) iff drift - lambda * S < 0,
equivalently lambda > drift / S.

Question: is there a *single* scalar lambda that contracts ALL known
artefact cycles?

  lambda_required(W) := drift(W) / S(W)
  lambda_max := max over witness corpus of lambda_required

If lambda_max < +infty within the corpus, lambda = lambda_max + epsilon
contracts every observed witness. (This is a *cycle-level* check, not a
global LP certificate; the LP must still locate a state-level
potential psi compatible with this lambda. That's iteration 068.)

We use exact rational arithmetic with LOG2_3_UPPER = Fraction(1584...,
10**15), so the threshold is a strict rational upper bound on the true
log_2 3 value. drift_q therefore upper-bounds the true drift; the
contractivity check `drift_q - lambda * S < 0` therefore upper-bounds
the true `drift - lambda * S < 0`. Sound.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "verifiers"))

from positivity_fuel import compose_affine  # noqa: E402

WITNESS_DIR = ROOT / "witnesses"
PROOF_DIR = ROOT / "proof_states"

LOG2_3_UPPER = Fraction(1584962500721157, 10**15)


def _detect_K(path: Path, data: dict) -> int:
    for tok in path.stem.split("_"):
        if tok.startswith("K") and tok[1:].isdigit():
            return int(tok[1:])
    return int(data.get("K") or 8)


def _extract_pi_middles_from_witness(cycle: dict, K: int) -> list[int]:
    edges = cycle.get("cycle_edges") or []
    out = []
    for e in edges:
        s = e.get("pi_middle") or e.get("pi_middle_int") or e.get("pi_middle_bin")
        if s is None:
            continue
        if isinstance(s, str):
            out.append(int(s, 2))
        else:
            out.append(int(s))
    return out


def gather_artefact_cycles() -> list[tuple[list[int], int, str]]:
    out = []
    for path in sorted(WITNESS_DIR.glob("iteration_*_cycle*.json")):
        if "_classified" in path.name:
            continue
        data = json.loads(path.read_text())
        K = _detect_K(path, data)
        for key in ("depth_free_witness", "lam_friendliest_witness"):
            cyc = data.get(key)
            if not cyc:
                continue
            pis = _extract_pi_middles_from_witness(cyc, K)
            if pis:
                out.append((pis, K, f"{path.name}::{key}"))
    for path in sorted(PROOF_DIR.glob("iteration_063_artifact_cegis_K*.json")):
        data = json.loads(path.read_text())
        K = _detect_K(path, data)
        for round_entry in data.get("rounds", []):
            cuts = round_entry.get("cuts")
            if not cuts:
                continue
            pis = []
            for cut in cuts:
                E1 = cut.get("E1")
                if E1 and len(E1) >= 4:
                    pis.append(int(E1[3]))
            if pis:
                out.append((pis, K, f"{path.name}::round_{round_entry.get('round')}"))
    return out


def required_lambda(pi_middles: list[int], K: int):
    """Returns (lambda_required: Fraction, A, B, S, T, m, drift_q) or None
    if the cycle is not positive-drift / not artefact.
    """
    A, B, S, T, m = compose_affine(pi_middles, K)
    if S == 0:
        return None
    denom = (1 << S) - A
    if denom >= 0:
        return None  # not negative-domain artefact
    # drift_q = m * (1 + LOG2_3_UPPER) - T   (rational upper bound on drift)
    drift_q = Fraction(m) * (Fraction(1) + LOG2_3_UPPER) - Fraction(T)
    if drift_q <= 0:
        return None  # negative-domain but not positive-drift; skip
    lam_req = drift_q / Fraction(S)
    return {
        "lambda_required": lam_req,
        "A": A, "B": B, "S": S, "T": T, "m": m,
        "denom": denom, "drift_q": drift_q,
    }


def main():
    t0 = time.time()
    cycles = gather_artefact_cycles()
    print(f"[067] gathered {len(cycles)} cycles")

    rows = []
    by_K = defaultdict(list)
    for pi_list, K, label in cycles:
        info = required_lambda(pi_list, K)
        if info is None:
            continue
        lam = info["lambda_required"]
        rows.append({
            "label": label, "K": K, "L": len(pi_list),
            "T": info["T"], "m": info["m"], "S": info["S"],
            "denom": info["denom"], "drift_q_str": str(info["drift_q"]),
            "drift_float": float(info["drift_q"]),
            "lambda_required_str": str(lam),
            "lambda_required_float": float(lam),
        })
        by_K[K].append(lam)

    if not rows:
        print("[067] no positive-drift artefact cycles found")
        return

    lam_max = max(r["lambda_required_str"] and Fraction(r["lambda_required_str"]) for r in rows)
    pad = Fraction(1, 100)
    lam_test = lam_max + pad

    # Verify every cycle contracts under lam_test.
    all_contract = True
    worst = None
    for r in rows:
        D = Fraction(r["drift_q_str"])
        S = Fraction(r["S"])
        delta_phi = D - lam_test * S
        if delta_phi >= 0:
            all_contract = False
            if worst is None or delta_phi > worst["delta_phi"]:
                worst = {**r, "delta_phi": delta_phi}

    # Per-K stats
    per_K = {}
    for K, lams in by_K.items():
        per_K[str(K)] = {
            "n_cycles": len(lams),
            "min_lambda_required": float(min(lams)),
            "max_lambda_required": float(max(lams)),
            "max_lambda_required_str": str(max(lams)),
        }

    # Determine the worst (highest-lambda) cycle:
    rows_sorted = sorted(rows, key=lambda r: r["lambda_required_float"], reverse=True)
    top5 = rows_sorted[:5]

    proof_state = {
        "proof_state": "iteration_067_eta_fuel_thresholds",
        "log2_3_upper_rational": [LOG2_3_UPPER.numerator, LOG2_3_UPPER.denominator],
        "lemma": (
            "Phi(n) := log_2(n) + lambda * eta_pi(n) is contractive "
            "around an artefact cycle iff drift - lambda * S < 0, "
            "equivalently lambda > drift / S. Drift uses the rational "
            "upper bound LOG2_3_UPPER, so the threshold is a sound "
            "upper bound for the true drift / S."
        ),
        "n_cycles_checked": len(rows),
        "max_lambda_required": float(lam_max),
        "max_lambda_required_str": str(lam_max),
        "lambda_test_used": float(lam_test),
        "lambda_test_used_str": str(lam_test),
        "all_artifact_cycles_contract_with_lambda": all_contract,
        "by_K": per_K,
        "top_5_by_lambda_required": top5,
        "worst_cycle_under_lambda_test": worst,
        "elapsed_seconds": time.time() - t0,
        "notes": (
            "This is cycle-level only, not a global LP certificate. "
            "If `all_artifact_cycles_contract_with_lambda` is true, then "
            "a single scalar lambda kills every known witness cycle. "
            "However, our witness corpus is finite; the question of "
            "whether *every* artefact cycle (across all closed walks of "
            "all lengths in the abstract graph) is contractible by this "
            "same lambda is OPEN. The boundary scaling drift/S = "
            "(r*log_2 3 + r - 1) / (1 - r) where r = m/T tends to "
            "+infinity as r -> 1, so a single global lambda may not "
            "exist for unbounded cycle 3-bias. The corpus result is "
            "informative about typical CEGIS witnesses."
        ),
    }

    out = PROOF_DIR / "iteration_067_eta_fuel.json"
    out.write_text(json.dumps(proof_state, indent=2))

    print(f"[067] cycles_checked          : {len(rows)}")
    print(f"[067] max_required_lambda     : {float(lam_max):.6f}")
    print(f"[067] all contract @ lam_test : {all_contract}")
    print(f"[067] per-K max_lambda        :")
    for K, s in per_K.items():
        print(f"        K={K} : n={s['n_cycles']} max_lambda={s['max_lambda_required']:.6f}")
    print(f"[067] top 5 by lambda required:")
    for r in top5:
        print(f"        lambda={r['lambda_required_float']:.4f}  K={r['K']} L={r['L']} m={r['m']} S={r['S']}  {r['label']}")
    print(f"[067] wrote {out}")


if __name__ == "__main__":
    main()
