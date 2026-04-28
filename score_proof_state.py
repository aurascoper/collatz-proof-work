"""Structured scorer for Collatz proof_state JSON.

Used by the autoresearch loop to rank runs without incentivising bogus
proof claims. Higher score = a better run.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def score(ps: dict) -> int:
    s = 0
    if ps.get("exact_rational_verified"):
        s += 1000
    if ps.get("closed_graph"):
        s += 500
    if ps.get("lp_feasible"):
        s += 200
    if ps.get("witness_extracted"):
        s += 100
    if ps.get("integer_realizable_single_orbit") is False:
        s += 50
    if ps.get("modeling_bug_found"):
        s += 75
    s -= 10 * int(ps.get("unexplained_failures", 0))
    return s


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: score_proof_state.py <proof_state.json> [...]", file=sys.stderr)
        return 1
    for path in argv[1:]:
        ps = json.loads(Path(path).read_text())
        print(f"{path}\tscore={score(ps)}\tstate={ps.get('proof_state')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
