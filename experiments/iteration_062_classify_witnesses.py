"""Iteration 062: classify all extracted witness cycles by affine
admissibility.

Walks `witnesses/iteration_*_cycle*.json`, extracts every cycle's
ordered list of `pi_middle` masks, runs `cycle_classifier.classify_cycle`,
and writes:

  - An updated witness file `<original>_classified.json` adding a
    `classification` block to each cycle.
  - A summary `proof_states/iteration_062_classifier.json`.

This iteration does NOT remove any constraints from any LP; it only
labels the witnesses as realisable or not (with the failure mode).

Re-running this iteration is idempotent: the original witness files are
left untouched; only `_classified.json` is overwritten.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "verifiers"))

from cycle_classifier import classify_cycle  # noqa: E402

WITNESS_DIR = ROOT / "witnesses"
PROOF_DIR = ROOT / "proof_states"
PROOF_DIR.mkdir(parents=True, exist_ok=True)


def _classify_one_cycle(cycle: dict, K: int) -> dict:
    """Classify a single cycle dict that contains `cycle_edges`."""
    if cycle is None:
        return None
    edges = cycle.get("cycle_edges") or []
    pi_strs = []
    for e in edges:
        s = e.get("pi_middle")
        if s is None:
            continue
        # Some entries are stored as binary strings, others as ints.
        if isinstance(s, str):
            pi_strs.append(s)
        else:
            pi_strs.append(format(int(s), f"0{K}b"))
    if not pi_strs:
        return {"classification": "no_pi_middles_present"}
    pis = [int(s, 2) for s in pi_strs]
    return classify_cycle(pis, K)


def _detect_K_from_path(path: Path) -> int:
    """Pull K out of filenames like `iteration_060c_cycle_K8.json`.

    Falls back to inspecting any `K`-shaped field inside the JSON if the
    filename does not encode K.
    """
    for tok in path.stem.split("_"):
        if tok.startswith("K") and tok[1:].isdigit():
            return int(tok[1:])
    data = json.loads(path.read_text())
    if "K" in data:
        return int(data["K"])
    raise ValueError(f"Cannot determine K for {path}")


def main():
    t0 = time.time()
    summary = []
    files = sorted(WITNESS_DIR.glob("iteration_*_cycle*.json"))
    files = [p for p in files if "_classified" not in p.name]
    print(f"[062] classifying {len(files)} witness files")

    for path in files:
        K = _detect_K_from_path(path)
        data = json.loads(path.read_text())
        modified = False

        for key in ("depth_free_witness", "lam_friendliest_witness"):
            cyc = data.get(key)
            if cyc is None:
                continue
            cls = _classify_one_cycle(cyc, K)
            cyc["classification"] = cls
            modified = True
            label = cls.get("classification") if cls else "(no cycle)"
            n_cand = cls.get("candidate_n") if cls else None
            print(
                f"  {path.name:<60} {key:<24} -> {label} "
                f"(n_candidate={n_cand}, denom={cls.get('denom_2S_minus_A')})"
            )
            summary.append({
                "witness_file": str(path.relative_to(ROOT)),
                "cycle_kind": key,
                "K": K,
                "cycle_length": cyc.get("cycle_length"),
                "classification": label,
                "denom": cls.get("denom_2S_minus_A"),
                "candidate_n": n_cand,
                "B_value": cls.get("B_value"),
                "A_3_to_m": cls.get("A_3_to_m"),
                "S_total_divisions": cls.get("S_total_divisions"),
            })

        if modified:
            out_path = path.with_name(path.stem + "_classified.json")
            out_path.write_text(json.dumps(data, indent=2))

    realisable = [s for s in summary if s["classification"] == "REALIZABLE_POSITIVE_INTEGER_CYCLE"]
    by_class = {}
    for s in summary:
        by_class.setdefault(s["classification"], 0)
        by_class[s["classification"]] += 1

    proof_state = {
        "proof_state": "iteration_062_cycle_admissibility_classifier",
        "n_witness_files": len(files),
        "n_cycles_classified": len(summary),
        "by_classification": by_class,
        "any_realisable_positive_integer_cycle": len(realisable) > 0,
        "realisable_witnesses": realisable,
        "all_witnesses": summary,
        "elapsed_seconds": time.time() - t0,
        "interpretation": (
            "Every previously extracted LP-infeasibility witness has been "
            "fed through the affine admissibility classifier. A witness is "
            "labelled REALIZABLE_POSITIVE_INTEGER_CYCLE only if its "
            "concatenated pi_middles compose to an affine map (2^S - 3^m) > 0 "
            "with B / denom a positive integer that direct arbitrary-precision "
            "Collatz simulation actually traces. If any such witness exists, "
            "we have a putative non-trivial Collatz cycle and must verify "
            "whether n is a known cycle (e.g. n=1) or new."
        ),
    }
    out = PROOF_DIR / "iteration_062_classifier.json"
    out.write_text(json.dumps(proof_state, indent=2))
    print(f"[062] wrote {out}")
    print(json.dumps(by_class, indent=2))


if __name__ == "__main__":
    main()
