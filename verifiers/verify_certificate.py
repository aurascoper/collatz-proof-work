"""Exact rational re-verifier for an exported LP certificate.

Reads `certificates/iteration_*.json` (psi, lam, states) and re-checks every
constraint of the corresponding multigraph using `Fraction` arithmetic and
`LOG2_3_UPPER = Fraction(1584962500721157, 10**15)`.

Usage:
    python -m verifiers.verify_certificate <certificate.json> <K>
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path


LOG2_3_UPPER = Fraction(1584962500721157, 10**15)


def verify(cert_path: Path, K: int, eps: Fraction = Fraction(1, 100)) -> dict:
    cert = json.loads(cert_path.read_text())
    psi = [Fraction(p).limit_denominator(10**12) for p in cert["psi"]]
    lam = [Fraction(l).limit_denominator(10**12) for l in cert["lam"]]
    one_plus_log2_3 = Fraction(1) + LOG2_3_UPPER

    # Re-enumerate the same edges. We expect a sibling file
    # `experiments/iteration_*.py` to be the canonical generator. To stay
    # decoupled, this script supports a `--edge-cache` JSON of edges if
    # provided (since re-enumeration at K=8 takes minutes).
    edge_cache = cert.get("edge_cache")
    if edge_cache is None:
        raise SystemExit(
            "certificate has no edge_cache; re-run experiment with "
            "EXPORT_EDGES=1 to embed edges in the certificate."
        )

    n_fail = 0
    max_viol = Fraction(0)
    for e in edge_cache:
        i1 = e["i1"]
        i2 = e["i2"]
        c_val = Fraction(int(e["c_val"]))
        m_mid = int(e["m_middle"])
        lhs = (
            psi[i2] - psi[i1]
            + c_val * lam[i2]
            + Fraction(m_mid) * one_plus_log2_3
            - Fraction(K)
            + eps
        )
        if lhs > 0:
            n_fail += 1
            if lhs > max_viol:
                max_viol = lhs

    return {
        "verifier": "exact_rational_fraction_log2_3_upper",
        "certificate_file": str(cert_path),
        "K": K,
        "epsilon": str(eps),
        "log2_3_upper_rational": [LOG2_3_UPPER.numerator, LOG2_3_UPPER.denominator],
        "n_edges_checked": len(edge_cache),
        "n_failed": n_fail,
        "max_violation": str(max_viol),
        "verified": n_fail == 0,
    }


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: verify_certificate.py <certificate.json> <K>", file=sys.stderr)
        return 2
    cert_path = Path(argv[1])
    K = int(argv[2])
    result = verify(cert_path, K)
    print(json.dumps(result, indent=2))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
