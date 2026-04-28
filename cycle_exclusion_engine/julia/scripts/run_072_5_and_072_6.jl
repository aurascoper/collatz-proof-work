#!/usr/bin/env julia
# Driver for Iteration 072.5 (theorem-filter pipeline) and 072.6
# (candidate analyzer). Reads paths and config from environment.

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

include(joinpath(@__DIR__, "..", "src", "CEEJulia.jl"))
using .CEEJulia

function main()
    ndjson_in = get(ENV, "CEE_PERIODIC_INPUT", "out/periodic_T24.ndjson")
    proof_0725 = get(ENV, "CEE_0725_PROOFSTATE",
                     "proof_states/iteration_072_5_baker_interface_T24.json")
    open_ndjson = get(ENV, "CEE_OPEN_CANDIDATES_NDJSON",
                      "candidates/iteration_072_5_open_candidates_T24.ndjson")
    open_json = get(ENV, "CEE_OPEN_CANDIDATES_JSON",
                    "candidates/iteration_072_5_open_candidates_T24.json")
    proof_0726 = get(ENV, "CEE_0726_PROOFSTATE",
                     "proof_states/iteration_072_6_candidate_analyzer_T24.json")

    cfg = default_theorem_config()
    analyzer_cfg = AnalyzerConfig(
        parse(Int, get(ENV, "CEE_ANALYZER_PRECISION_BITS", "512")),
        parse(Int, get(ENV, "CEE_ANALYZER_SHORTLIST_SIZE", "50")),
    )

    println("=== Iteration 072.5 ===")
    println("Input NDJSON  : ", ndjson_in)
    println("Proof-state   : ", proof_0725)
    println("Open NDJSON   : ", open_ndjson)
    println("Open JSON     : ", open_json)

    proof_state, rows, open_candidates = run_periodic_pipeline(
        ndjson_in;
        cfg = cfg,
        apply_baker = true,
        output_path = proof_0725,
    )

    n_ndjson = export_open_candidates_ndjson(rows, open_ndjson)
    n_json   = export_open_candidates_json(rows, open_json)

    println("072.5 summary:")
    for k in sort(collect(keys(proof_state)))
        if k != "rows"
            println("  $k => ", proof_state[k])
        end
    end
    println("Exported OPEN_CANDIDATE rows: NDJSON=$(n_ndjson) JSON=$(n_json)")
    println()

    println("=== Iteration 072.6 ===")
    println("Proof-state   : ", proof_0726)
    if n_ndjson == 0
        empty_rows = Dict[]
        export_ranked_candidates_json(empty_rows, proof_0726; cfg = analyzer_cfg)
        println("No OPEN_CANDIDATE rows. Wrote empty analyzer proof_state.")
        return 0
    end

    analyzed = analyze_open_candidates_ndjson(open_ndjson; cfg = analyzer_cfg)
    export_ranked_candidates_json(analyzed, proof_0726; cfg = analyzer_cfg)
    println("Analyzed candidates: ", length(analyzed))
    if !isempty(analyzed)
        top = analyzed[1]
        println("Top-ranked candidate:")
        println("  word_bits = ", top["word_bits"])
        println("  T m S     = ", top["T"], " ", top["m"], " ", top["S"])
        println("  delta     = ", top["delta_str"])
        println("  ratio_gap = ", top["ratio_gap_str"])
    end
    return 0
end

exit(main())
