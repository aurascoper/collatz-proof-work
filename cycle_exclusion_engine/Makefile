.PHONY: help test bench cycle-engine cycle-engine-json clean

help:
	@echo "Cycle Exclusion Engine targets:"
	@echo "  make test               -- run Rust + Julia unit tests"
	@echo "  make bench              -- benchmark Rust generator at K=24, K=36"
	@echo "  make cycle-engine       -- run shell pipeline (T<=24 by default)"
	@echo "  make cycle-engine-json  -- run Python pipeline with manifest JSON"
	@echo "  make clean              -- remove out/, logs/, manifests/"

test:
	cd rust && cargo test --release
	cd julia && julia --project=. test/runtests.jl

bench:
	cd rust && cargo run --release --bin cee_generate -- --K 24 --benchmark
	cd rust && cargo run --release --bin cee_generate -- --K 36 --benchmark

cycle-engine:
	./scripts/run_cycle_engine.sh

cycle-engine-json:
	python3 scripts/run_cycle_engine.py

clean:
	rm -rf out/ logs/ manifests/
