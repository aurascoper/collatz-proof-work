"""Iteration 065: structural analysis of the negative-domain artefact family.

Reads `proof_states/iteration_063_artifact_cegis_K*.json` and produces
combinatorial statistics:

  - Number of distinct (m, S) classes among cycles cut.
  - Distribution of cycle lengths.
  - Distribution of |denom| = 3^m - 2^S magnitudes.
  - Smallest |denom| seen (the "least pathological" artefact).
  - Whether classifications EVER change away from
    `non_realizable_negative_or_zero_denom`.

Goal: characterise the artefact family quantitatively, so the
positivity-aware reformulation has hard targets.

This iteration writes `proof_states/iteration_065_family_analysis.json`
and emits a short human-readable summary. NO Collatz claim is made.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROOF_DIR = ROOT / "proof_states"


def main():
    t0 = time.time()
    files = sorted(PROOF_DIR.glob("iteration_063_artifact_cegis_K*.json"))
    if not files:
        print("[065] no 063 results found")
        return

    by_K = defaultdict(list)
    for f in files:
        d = json.loads(f.read_text())
        by_K[d["K"]].append((f, d))

    summary = {}
    for K, items in sorted(by_K.items()):
        # Take the run with the most rounds
        items.sort(key=lambda kv: kv[1].get("n_rounds_executed", 0), reverse=True)
        path, data = items[0]

        rounds = data.get("rounds", [])
        cls_counter = Counter(r.get("classification") for r in rounds if r.get("classification"))
        len_counter = Counter(r.get("cycle_length") for r in rounds if r.get("cycle_length"))
        m_S_classes = Counter(
            (r.get("cycle_length"), r.get("S_total_divisions"))
            for r in rounds
            if r.get("cycle_length") and r.get("S_total_divisions") is not None
        )
        denom_magnitudes = [
            abs(r["denom"]) for r in rounds if r.get("denom") is not None
        ]
        denom_signs = Counter(
            "neg" if r.get("denom") is not None and r["denom"] < 0
            else ("pos" if r.get("denom") is not None and r["denom"] > 0
                  else "zero")
            for r in rounds
            if r.get("denom") is not None
        )

        smallest_denom_mag = min(denom_magnitudes) if denom_magnitudes else None
        largest_denom_mag = max(denom_magnitudes) if denom_magnitudes else None

        # Did classification ever change away from negative_or_zero_denom?
        labels_seen = list(cls_counter.keys())
        ever_realizable = "REALIZABLE_POSITIVE_INTEGER_CYCLE" in labels_seen
        ever_non_integer_with_pos_denom = (
            "non_realizable_non_integer_fixed_point" in labels_seen
        )

        summary[K] = {
            "source_file": str(path.relative_to(ROOT)),
            "n_rounds": data.get("n_rounds_executed"),
            "final_status": data.get("final_status"),
            "n_active_edges_remaining": (
                rounds[-1].get("n_active_edges") if rounds else None
            ),
            "n_blocked_edges_total": (
                rounds[-1].get("n_blocked_edges") if rounds else None
            ),
            "classification_histogram": dict(cls_counter),
            "cycle_length_histogram": dict(len_counter),
            "n_distinct_(L,S)_classes": len(m_S_classes),
            "denom_sign_histogram": dict(denom_signs),
            "smallest_|denom|": smallest_denom_mag,
            "largest_|denom|": largest_denom_mag,
            "ever_realizable_positive_int_cycle": ever_realizable,
            "ever_non_integer_with_positive_denom": ever_non_integer_with_pos_denom,
            "every_witness_is_negative_domain_artefact": (
                set(labels_seen) == {"non_realizable_negative_or_zero_denom"}
            ),
        }

    overall = {
        "proof_state": "iteration_065_artefact_family_analysis",
        "by_K": summary,
        "elapsed_seconds": time.time() - t0,
        "interpretation": (
            "Quantifies the negative-domain artefact family encountered "
            "by the 063 CEGIS loop. If `every_witness_is_negative_domain"
            "_artefact` is true and `ever_realizable_positive_int_cycle` "
            "is false at every K examined, then the LP infeasibility in "
            "the (r, pi) abstraction is structurally explained by the "
            "positivity-domain theorem (064) and contains no Collatz "
            "signal. The next move is a positivity-aware reformulation "
            "(future Iteration 066+) rather than further cuts."
        ),
    }
    out = PROOF_DIR / "iteration_065_family_analysis.json"
    out.write_text(json.dumps(overall, indent=2))
    for K, s in summary.items():
        print(f"--- K={K} (rounds={s['n_rounds']}) ---")
        print(f"  every artefact?       {s['every_witness_is_negative_domain_artefact']}")
        print(f"  classification hist:  {s['classification_histogram']}")
        print(f"  cycle-length hist:    {s['cycle_length_histogram']}")
        print(f"  denom-sign hist:      {s['denom_sign_histogram']}")
        print(f"  smallest |denom|:     {s['smallest_|denom|']}")
        print(f"  largest |denom|:      {s['largest_|denom|']}")
    print(f"[065] wrote {out}")


if __name__ == "__main__":
    main()
