module CEEJulia

using JSON

# Iteration 072 + 072.5 + 072.6
include("periodic_reader.jl")
include("exact_classifier_periodic.jl")
include("baker_interface.jl")
include("candidate_export.jl")
include("pipeline_periodic.jl")
include("candidate_analyzer.jl")

# Periodic / 072 exports
export PeriodicRecord, ClassificationResult
export read_periodic_ndjson, classify_fixed_point_periodic, verify_collatz_cycle_periodic

# 072.5 exports
export BakerInput, BakerVerdict, TheoremConfig, default_theorem_config
export build_baker_input, apply_verified_bound, apply_oddstep_bound, apply_baker_bound
export run_periodic_pipeline
export export_open_candidates_ndjson, export_open_candidates_json,
       candidate_row_to_export_dict

# 072.6 exports
export AnalyzerConfig, default_analyzer_config
export analyze_candidate, analyze_open_candidates_ndjson, export_ranked_candidates_json

end # module
