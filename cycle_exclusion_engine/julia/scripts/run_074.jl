#!/usr/bin/env julia
# Iteration 074 driver: theorem-layer-only pipeline.
# Runs the periodic-cycle pipeline with the Baker theorem dispatcher
# enabled and writes a 074-flavored proof_state plus OPEN_CANDIDATE
# exports. Skips the 072.6 candidate analyzer (caller may run it
# separately if OPEN_CANDIDATE > 0).

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

include(joinpath(@__DIR__, "..", "src", "CEEJulia.jl"))
using .CEEJulia

function main()
    ndjson_in   = get(ENV, "CEE_PERIODIC_INPUT", "out/periodic_T24.ndjson")
    proof_074   = get(ENV, "CEE_074_PROOFSTATE",
                      "proof_states/iteration_074_theorem_layer_T24.json")
    open_ndjson = get(ENV, "CEE_074_OPEN_NDJSON",
                      "candidates/iteration_074_open_candidates_T24.ndjson")
    open_json   = get(ENV, "CEE_074_OPEN_JSON",
                      "candidates/iteration_074_open_candidates_T24.json")

    cfg = default_theorem_config()
    mkpath(dirname(proof_074))
    mkpath(dirname(open_ndjson))
    mkpath(dirname(open_json))

    println("=== Iteration 074 (theorem-layer-only) ===")
    println("Input NDJSON  : ", ndjson_in)
    println("Proof-state   : ", proof_074)
    println("Open NDJSON   : ", open_ndjson)
    println("Open JSON     : ", open_json)

    proof_state, rows, open_candidates = run_periodic_pipeline(
        ndjson_in;
        cfg = cfg,
        apply_baker = true,
        output_path = proof_074,
    )

    n_ndjson = export_open_candidates_ndjson(rows, open_ndjson)
    n_json   = export_open_candidates_json(rows, open_json)

    println()
    println("074 summary:")
    for k in sort(collect(keys(proof_state)))
        println("  $k => ", proof_state[k])
    end
    println()
    println("Exported OPEN_CANDIDATE rows:")
    println("  NDJSON : $(n_ndjson) -> $(open_ndjson)")
    println("  JSON   : $(n_json) -> $(open_json)")
    println("Open candidates returned by pipeline: ", length(open_candidates))
    return 0
end

exit(main())
