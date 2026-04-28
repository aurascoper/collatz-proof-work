#!/usr/bin/env bash
# Top-level shell runner: Rust generator -> Julia 072.5+072.6 pipeline.
set -euo pipefail

T_MIN="${T_MIN:-1}"
T_MAX="${T_MAX:-24}"
PRIMITIVE_ONLY="${PRIMITIVE_ONLY:-true}"

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
RUST_DIR="${RUST_DIR:-$ROOT_DIR/rust}"
JULIA_DIR="${JULIA_DIR:-$ROOT_DIR/julia}"

RUN_TAG="${RUN_TAG:-T${T_MAX}}"

OUT_DIR="${OUT_DIR:-$ROOT_DIR/out}"
LOG_DIR="${LOG_DIR:-$ROOT_DIR/logs}"
PROOF_DIR="${PROOF_DIR:-$ROOT_DIR/proof_states}"
CAND_DIR="${CAND_DIR:-$ROOT_DIR/candidates}"

mkdir -p "$OUT_DIR" "$LOG_DIR" "$PROOF_DIR" "$CAND_DIR"

NDJSON_OUT="${NDJSON_OUT:-$OUT_DIR/periodic_${RUN_TAG}.ndjson}"
PROOF_0725="${PROOF_0725:-$PROOF_DIR/iteration_072_5_baker_interface_${RUN_TAG}.json}"
OPEN_NDJSON="${OPEN_NDJSON:-$CAND_DIR/iteration_072_5_open_candidates_${RUN_TAG}.ndjson}"
OPEN_JSON="${OPEN_JSON:-$CAND_DIR/iteration_072_5_open_candidates_${RUN_TAG}.json}"
PROOF_0726="${PROOF_0726:-$PROOF_DIR/iteration_072_6_candidate_analyzer_${RUN_TAG}.json}"

ANALYZER_PRECISION_BITS="${ANALYZER_PRECISION_BITS:-512}"
ANALYZER_SHORTLIST_SIZE="${ANALYZER_SHORTLIST_SIZE:-50}"

RUST_LOG="${RUST_LOG:-$LOG_DIR/rust_generate_${RUN_TAG}.log}"
JULIA_LOG="${JULIA_LOG:-$LOG_DIR/julia_pipeline_${RUN_TAG}.log}"

ts()  { date "+%Y-%m-%d %H:%M:%S"; }
sec() { python3 -c 'import time; print(time.time())'; }

echo "[$(ts)] Cycle Exclusion Engine runner starting"
echo "ROOT_DIR=$ROOT_DIR  RUN_TAG=$RUN_TAG  T_MIN=$T_MIN  T_MAX=$T_MAX  PRIMITIVE_ONLY=$PRIMITIVE_ONLY"

echo "[$(ts)] Stage 1: Rust periodic generator"
t1s=$(sec)
(
  cd "$RUST_DIR"
  cargo run --release --bin cee_periodic_generate -- \
    --t-min "$T_MIN" --t-max "$T_MAX" \
    --primitive-only "$PRIMITIVE_ONLY" \
    --output "$NDJSON_OUT"
) 2>&1 | tee "$RUST_LOG"
t1e=$(sec)
echo "[$(ts)] Stage 1 done in $(python3 -c "print(${t1e} - ${t1s})") s"

echo "[$(ts)] Stage 2: Julia 072.5 + 072.6"
t2s=$(sec)
(
  cd "$ROOT_DIR"
  CEE_PERIODIC_INPUT="$NDJSON_OUT" \
  CEE_0725_PROOFSTATE="$PROOF_0725" \
  CEE_OPEN_CANDIDATES_NDJSON="$OPEN_NDJSON" \
  CEE_OPEN_CANDIDATES_JSON="$OPEN_JSON" \
  CEE_0726_PROOFSTATE="$PROOF_0726" \
  CEE_ANALYZER_PRECISION_BITS="$ANALYZER_PRECISION_BITS" \
  CEE_ANALYZER_SHORTLIST_SIZE="$ANALYZER_SHORTLIST_SIZE" \
  julia --project="$JULIA_DIR" "$JULIA_DIR/scripts/run_072_5_and_072_6.jl"
) 2>&1 | tee "$JULIA_LOG"
t2e=$(sec)
echo "[$(ts)] Stage 2 done in $(python3 -c "print(${t2e} - ${t2s})") s"

echo
echo "Artifacts:"
echo "  NDJSON              $NDJSON_OUT"
echo "  Proof 072.5         $PROOF_0725"
echo "  Open NDJSON         $OPEN_NDJSON"
echo "  Open JSON           $OPEN_JSON"
echo "  Proof 072.6         $PROOF_0726"
echo
echo "Logs:"
echo "  Rust                $RUST_LOG"
echo "  Julia               $JULIA_LOG"
