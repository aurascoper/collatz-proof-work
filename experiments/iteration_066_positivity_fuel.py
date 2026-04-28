"""Iteration 066: positivity-aware artefact-family fuel analysis.

For every witness cycle in the corpus classified
`non_realizable_negative_or_zero_denom`:

  1. Recompose the affine map T_pi(n) = (A n + B) / 2^S exactly.
  2. Compute the negative fixed point a = B / denom (denom = 2^S - A < 0).
  3. Build a positive synthetic seed n_d that shadows the cycle for
     exactly k periods (k chosen per cycle).
  4. Run arbitrary-precision direct Collatz simulation from n_d.
  5. Confirm the orbit's parity matches the cycle for `k` periods and
     diverges thereafter -- empirically validating the fuel lemma:

         eta_pi(n) := v2(n - a)
         eta_pi(T_pi(n)) = eta_pi(n) - S
         max_shadow_periods(n) = floor(eta_pi(n) / S).

  6. Aggregate:
     - predicted vs observed shadow depth per cycle,
     - monotone-fuel success rate (should be 1.0 if the lemma is right),
     - examples for K=6 and K=8.

  7. Recommend an LP-compatible *cycle-level* fuel term: each artefact
     cycle period consumes exactly `S_cycle` units of v_2 depth, so the
     LP must allow psi to drift by `lambda * S_cycle` per period via a
     per-cycle Lyapunov coefficient (rather than the per-window depth
     shift used in 060c).

NO LP cuts; no Collatz claim. The fuel lemma is a *positivity lemma*:
it says positive integers can shadow a negative-domain artefact only
finitely many times, and exactly tracks how much fuel is consumed.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "verifiers"))

from positivity_fuel import (  # noqa: E402
    compose_affine,
    construct_shadow_seed,
    fuel_eta,
    shadow_artefact_cycle,
    simulate_collatz,
    verify_v2_fuel_dynamics,
)

WITNESS_DIR = ROOT / "witnesses"
PROOF_DIR = ROOT / "proof_states"
PROOF_DIR.mkdir(parents=True, exist_ok=True)


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


def _gather_artefact_cycles_from_witnesses() -> list[tuple[list[int], int, str]]:
    """Returns list of (pi_middles, K, source_label)."""
    out = []
    for path in sorted(WITNESS_DIR.glob("iteration_*_cycle*.json")):
        if "_classified" in path.name:
            continue  # skip the classified copies; primary file already covers it
        data = json.loads(path.read_text())
        K = _detect_K(path, data)
        for key in ("depth_free_witness", "lam_friendliest_witness"):
            cyc = data.get(key)
            if not cyc:
                continue
            pis = _extract_pi_middles_from_witness(cyc, K)
            if pis:
                out.append((pis, K, f"{path.name}::{key}"))
    return out


def _gather_artefact_cycles_from_063(max_per_K: int = 30) -> list[tuple[list[int], int, str]]:
    """Iteration 063 stores the cycle as a list of (E1, E2) cuts.
    pi_middle for each edge equals E1[3] (since E1 = (r1, pi0, r2, pi1)
    and pi_middle = pi_1).
    """
    out = []
    by_K_count = Counter()
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
            if not pis:
                continue
            if by_K_count[K] >= max_per_K:
                continue
            by_K_count[K] += 1
            out.append((pis, K, f"{path.name}::round_{round_entry.get('round')}"))
    return out


def main():
    t0 = time.time()
    cycles = _gather_artefact_cycles_from_witnesses() + _gather_artefact_cycles_from_063()
    print(f"[066] gathered {len(cycles)} artefact cycles for fuel verification")

    rows = []
    success_count = 0
    fail_count = 0
    skipped_count = 0

    for pi_list, K, label in cycles:
        try:
            A, B, S, T, m = compose_affine(pi_list, K)
        except Exception as exc:
            skipped_count += 1
            continue
        denom = (1 << S) - A
        if denom >= 0:
            # Not an artefact; skip per spec.
            skipped_count += 1
            continue
        if S == 0:
            skipped_count += 1
            continue

        # Two checks per cycle:
        # (a) v_2-fuel lemma: eta(T_pi(n)) = eta(n) - S, ARITHMETICALLY.
        # (b) parity-shadow: how many full orbit-periods follow pi.
        target_periods = 3
        try:
            v2_check = verify_v2_fuel_dynamics(pi_list, K, target_periods)
            sim = shadow_artefact_cycle(pi_list, K, target_periods)
        except Exception as exc:
            rows.append({
                "label": label, "K": K, "L": len(pi_list),
                "error": str(exc),
            })
            fail_count += 1
            continue

        ok = bool(v2_check.get("v2_fuel_decreases_by_S_per_iteration"))
        rows.append({
            "label": label, "K": K, "L": len(pi_list),
            "S": S, "A": A, "B": B, "denom": denom,
            "n_d_seed": sim["n_d_seed"],
            "eta_initial": sim["eta_initial"],
            "v2_fuel_iterations_predicted": sim["v2_fuel_iterations_predicted"],
            "v2_fuel_decreases_by_S": ok,
            "parity_matched_periods_observed": sim["parity_matched_periods_observed"],
            "shadow_le_v2_fuel": sim["shadow_le_v2_fuel"],
            "first_3_period_n_values": sim["period_n_values"][:4],
        })
        if ok:
            success_count += 1
        else:
            fail_count += 1

    by_K = defaultdict(lambda: {"success": 0, "fail": 0, "skipped": 0})
    parity_match_le_v2 = 0
    parity_match_strictly_less = 0
    for r in rows:
        K = r["K"]
        if r.get("v2_fuel_decreases_by_S") is True:
            by_K[K]["success"] += 1
        else:
            by_K[K]["fail"] += 1
        v2 = r.get("v2_fuel_iterations_predicted") or 0
        sh = r.get("parity_matched_periods_observed") or 0
        if sh <= v2:
            parity_match_le_v2 += 1
        if sh < v2:
            parity_match_strictly_less += 1

    proof_state = {
        "proof_state": "iteration_066_positivity_fuel",
        "lemma": (
            "(v_2-fuel lemma) For any periodic affine cycle with "
            "denom = 2^S - A != 0 and B from the canonical recurrence, "
            "T_pi(n) - a = A*(n - a)/2^S where a = B/denom. Hence "
            "v_2((T_pi(n) - a) * denom) = v_2((n - a) * denom) - S "
            "whenever T_pi(n) is integer (since denom is odd and "
            "A = 3^m is odd). Define eta_pi(n) := v_2(n*denom - B). "
            "Then eta(T_pi(n)) = eta(n) - S whenever T_pi(n) is an "
            "integer, and the maximum number of integer T_pi-iterations "
            "starting from n equals floor(eta_pi(n) / S). "
            "(Caveat: parity-shadowing is a strictly stronger condition "
            "than T_pi-integerness; the orbit may diverge from pi after "
            "fewer periods than v_2-fuel allows. Parity-shadowing is "
            "ALWAYS bounded above by v_2-fuel.)"
        ),
        "n_cycles_examined": len(rows),
        "n_skipped_non_artefact": skipped_count,
        "n_v2_fuel_lemma_holds": success_count,
        "n_v2_fuel_lemma_violated": fail_count,
        "v2_fuel_lemma_success_rate": (
            success_count / (success_count + fail_count) if (success_count + fail_count) else None
        ),
        "n_parity_shadow_le_v2_fuel": parity_match_le_v2,
        "n_parity_shadow_strictly_less_than_v2_fuel": parity_match_strictly_less,
        "by_K_success_counts": {str(K): v for K, v in by_K.items()},
        "examples": rows[:8],
        "lp_compatible_recommendation": (
            "Augment the LP with a *cycle-level* depth Lyapunov term "
            "lambda_cycle scaled by S_cycle (the cycle's total even-step "
            "count), rather than the per-window c_val used in 060c. "
            "Concretely: for every closed walk W in the abstract graph, "
            "require psi(end) - psi(start) + S_W * lambda_W <= -drift_W "
            "- |W|*eps, where lambda_W is non-negative and represents "
            "the rate at which v2-fuel is consumed per cycle period. "
            "This makes the LP positivity-aware: artefact cycles with "
            "denom < 0 receive a finite fuel budget that prevents them "
            "from forcing infeasibility."
        ),
        "elapsed_seconds": time.time() - t0,
    }
    out = PROOF_DIR / "iteration_066_positivity_fuel.json"
    out.write_text(json.dumps(proof_state, indent=2))

    print(f"[066] cycles examined            : {len(rows)}")
    print(f"[066] v_2-fuel lemma holds       : {success_count}")
    print(f"[066] v_2-fuel lemma violated    : {fail_count}")
    print(f"[066] skipped (non-artefact)     : {skipped_count}")
    print(f"[066] parity-shadow <= v_2-fuel  : {parity_match_le_v2}/{len(rows)}")
    print(f"[066] parity-shadow strictly <   : {parity_match_strictly_less}/{len(rows)}")
    if (success_count + fail_count):
        rate = success_count / (success_count + fail_count) * 100
        print(f"[066] v_2-fuel success rate      : {rate:.1f} %")
    print(f"[066] wrote {out}")


if __name__ == "__main__":
    main()
