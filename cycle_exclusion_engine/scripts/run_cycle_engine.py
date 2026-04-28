#!/usr/bin/env python3
"""Top-level Python runner with manifest. Runs Rust generator + Julia
072.5+072.6 pipeline, captures timings and exit codes, writes a single
machine-readable manifest JSON suitable for downstream tooling."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def run_cmd(
    cmd: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    log_path: Path | None = None,
) -> dict[str, Any]:
    start = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
    )
    end = time.time()
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            f"$ {' '.join(shlex.quote(x) for x in cmd)}\n\n"
            f"--- STDOUT ---\n{proc.stdout}\n"
            f"--- STDERR ---\n{proc.stderr}\n"
        )
    return {
        "cmd": cmd,
        "cwd": str(cwd) if cwd else None,
        "returncode": proc.returncode,
        "elapsed_seconds": end - start,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "ok": proc.returncode == 0,
    }


def env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


def env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def main() -> int:
    t0 = time.time()
    root_dir = Path(env_str("ROOT_DIR", str(Path(__file__).resolve().parents[1])))
    rust_dir = Path(env_str("RUST_DIR", str(root_dir / "rust")))
    julia_dir = Path(env_str("JULIA_DIR", str(root_dir / "julia")))

    t_min = int(env_str("T_MIN", "1"))
    t_max = int(env_str("T_MAX", "24"))
    primitive_only = env_bool("PRIMITIVE_ONLY", True)
    run_tag = env_str("RUN_TAG", f"T{t_max}")

    out_dir = Path(env_str("OUT_DIR", str(root_dir / "out")))
    log_dir = Path(env_str("LOG_DIR", str(root_dir / "logs")))
    proof_dir = Path(env_str("PROOF_DIR", str(root_dir / "proof_states")))
    cand_dir = Path(env_str("CAND_DIR", str(root_dir / "candidates")))
    manifest_dir = Path(env_str("MANIFEST_DIR", str(root_dir / "manifests")))
    for d in (out_dir, log_dir, proof_dir, cand_dir, manifest_dir):
        d.mkdir(parents=True, exist_ok=True)

    ndjson_out = Path(env_str("NDJSON_OUT", str(out_dir / f"periodic_{run_tag}.ndjson")))
    proof_0725 = Path(env_str("PROOF_0725",
                              str(proof_dir / f"iteration_072_5_baker_interface_{run_tag}.json")))
    open_ndjson = Path(env_str("OPEN_NDJSON",
                               str(cand_dir / f"iteration_072_5_open_candidates_{run_tag}.ndjson")))
    open_json = Path(env_str("OPEN_JSON",
                             str(cand_dir / f"iteration_072_5_open_candidates_{run_tag}.json")))
    proof_0726 = Path(env_str("PROOF_0726",
                              str(proof_dir / f"iteration_072_6_candidate_analyzer_{run_tag}.json")))
    rust_log = Path(env_str("RUST_LOG", str(log_dir / f"rust_generate_{run_tag}.log")))
    julia_log = Path(env_str("JULIA_LOG", str(log_dir / f"julia_pipeline_{run_tag}.log")))
    manifest_path = Path(env_str("MANIFEST_PATH",
                                 str(manifest_dir / f"run_cycle_engine_{run_tag}.json")))
    analyzer_precision_bits = env_str("ANALYZER_PRECISION_BITS", "512")
    analyzer_shortlist_size = env_str("ANALYZER_SHORTLIST_SIZE", "50")

    manifest: dict[str, Any] = {
        "proof_state": "run_cycle_engine_manifest",
        "started_at_unix": t0,
        "config": {
            "root_dir": str(root_dir),
            "rust_dir": str(rust_dir),
            "julia_dir": str(julia_dir),
            "t_min": t_min,
            "t_max": t_max,
            "primitive_only": primitive_only,
            "run_tag": run_tag,
            "analyzer_precision_bits": analyzer_precision_bits,
            "analyzer_shortlist_size": analyzer_shortlist_size,
        },
        "artifacts": {
            "ndjson_out": str(ndjson_out),
            "proof_0725": str(proof_0725),
            "open_ndjson": str(open_ndjson),
            "open_json": str(open_json),
            "proof_0726": str(proof_0726),
            "rust_log": str(rust_log),
            "julia_log": str(julia_log),
        },
        "stages": {},
    }

    # Stage 1: Rust generator
    rust_cmd = [
        "cargo", "run", "--release", "--bin", "cee_periodic_generate", "--",
        "--t-min", str(t_min), "--t-max", str(t_max),
        "--primitive-only", "true" if primitive_only else "false",
        "--output", str(ndjson_out),
    ]
    manifest["stages"]["rust_generator"] = run_cmd(
        rust_cmd, cwd=rust_dir, log_path=rust_log,
    )
    if not manifest["stages"]["rust_generator"]["ok"]:
        manifest["status"] = "failed"
        manifest["failed_stage"] = "rust_generator"
        manifest["finished_at_unix"] = time.time()
        manifest["total_elapsed_seconds"] = manifest["finished_at_unix"] - t0
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"Rust stage failed. Manifest: {manifest_path}", file=sys.stderr)
        return 1

    # Stage 2: Julia driver
    julia_env = os.environ.copy()
    julia_env.update({
        "CEE_PERIODIC_INPUT": str(ndjson_out),
        "CEE_0725_PROOFSTATE": str(proof_0725),
        "CEE_OPEN_CANDIDATES_NDJSON": str(open_ndjson),
        "CEE_OPEN_CANDIDATES_JSON": str(open_json),
        "CEE_0726_PROOFSTATE": str(proof_0726),
        "CEE_ANALYZER_PRECISION_BITS": analyzer_precision_bits,
        "CEE_ANALYZER_SHORTLIST_SIZE": analyzer_shortlist_size,
    })
    julia_cmd = [
        "julia", f"--project={julia_dir}",
        str(julia_dir / "scripts" / "run_072_5_and_072_6.jl"),
    ]
    manifest["stages"]["julia_pipeline"] = run_cmd(
        julia_cmd, cwd=root_dir, env=julia_env, log_path=julia_log,
    )
    manifest["status"] = "ok" if manifest["stages"]["julia_pipeline"]["ok"] else "failed"
    if not manifest["stages"]["julia_pipeline"]["ok"]:
        manifest["failed_stage"] = "julia_pipeline"

    # Pull proof_state summaries if present. Some artefacts nest the
    # summary under "proof_state" (072.5 layout); others put the
    # iteration label as the "proof_state" value with the summary at
    # the top level (072.6 layout). Handle both.
    for key, path in {
        "proof_0725_summary": proof_0725,
        "proof_0726_summary": proof_0726,
    }.items():
        if path.exists():
            try:
                data = json.loads(path.read_text())
                ps = data.get("proof_state", data)
                manifest[key] = ps if isinstance(ps, dict) else data
            except Exception as exc:
                manifest[key] = {"error": f"failed_to_parse: {exc}"}

    manifest["finished_at_unix"] = time.time()
    manifest["total_elapsed_seconds"] = manifest["finished_at_unix"] - t0
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(json.dumps({
        "status": manifest["status"],
        "run_tag": run_tag,
        "manifest_path": str(manifest_path),
        "total_elapsed_seconds": manifest["total_elapsed_seconds"],
    }, indent=2))
    return 0 if manifest["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
