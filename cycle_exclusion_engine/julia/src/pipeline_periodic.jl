using JSON

# Helper imported from candidate_export.jl (loaded later in CEEJulia.jl)
# but we redeclare a local copy if not yet loaded:
if !@isdefined(_verdict_to_dict)
    function _verdict_to_dict(v::Union{BakerVerdict, Nothing})
        if v === nothing
            return nothing
        end
        return Dict(
            "status" => String(v.status),
            "theorem_source" => v.theorem_source,
            "theorem_version" => v.theorem_version,
            "lower_bound_expr" => v.lower_bound_expr,
            "exclusion_reason" => v.exclusion_reason,
            "numeric_gap_str" => v.numeric_gap_str,
            "threshold_data" => v.threshold_data,
            "notes" => v.notes,
        )
    end
end

"""
    run_periodic_pipeline(ndjson_path; cfg, apply_baker, output_path)
        -> (proof_state::Dict, rows::Vector{Dict}, open_candidates::Vector)

Iteration 072.5 main entry. For each periodic record from the NDJSON
file emitted by the Rust generator, classify the affine fixed point,
optionally invoke the Baker theorem dispatcher, and emit a proof_state
plus per-row diagnostics.
"""
function run_periodic_pipeline(ndjson_path::AbstractString;
                                cfg::TheoremConfig = default_theorem_config(),
                                apply_baker::Bool = true,
                                output_path::Union{Nothing, AbstractString} = nothing)
    records = read_periodic_ndjson(ndjson_path)
    counts = Dict(
        "NEGATIVE_OR_ZERO_DENOM" => 0,
        "NON_INTEGER_FIXED_POINT" => 0,
        "NON_POSITIVE_FIXED_POINT" => 0,
        "REALIZABLE_TRIVIAL" => 0,
        "REALIZABLE_CANDIDATE" => 0,
        "EXCLUDED_BY_FINITE_VERIFICATION" => 0,
        "EXCLUDED_BY_THEOREM" => 0,
        "OPEN_CANDIDATE" => 0,
    )
    rows = Dict[]
    open_candidates = Dict[]

    for rec in records
        result = classify_fixed_point_periodic(rec)
        base_cls = result.classification
        n = result.n_candidate

        baker_verdict = nothing
        final_cls = base_cls

        if apply_baker
            inp = build_baker_input(rec, result)
            baker_verdict = apply_baker_bound(inp; cfg = cfg)
            if baker_verdict.status == :excluded_by_verified_bound
                final_cls = "EXCLUDED_BY_FINITE_VERIFICATION"
            elseif baker_verdict.status == :excluded_by_theorem
                final_cls = "EXCLUDED_BY_THEOREM"
            elseif baker_verdict.status == :open_candidate &&
                   base_cls == "REALIZABLE_CANDIDATE"
                final_cls = "OPEN_CANDIDATE"
            end
        end

        counts[final_cls] = get(counts, final_cls, 0) + 1
        row = Dict(
            "word_bits" => rec.word_bits,
            "canonical_rotation" => rec.canonical_rotation,
            "T" => rec.T,
            "m" => rec.m,
            "S" => rec.S,
            "classification" => final_cls,
            "n_candidate_str" => isnothing(n) ? nothing : string(n),
            "baker_verdict" => _verdict_to_dict(baker_verdict),
            "notes" => result.notes,
        )
        push!(rows, row)
        if final_cls == "OPEN_CANDIDATE"
            push!(open_candidates, candidate_row_to_export_dict(row))
        end
    end

    nontriv_realizable = [r for r in rows
                          if r["classification"] == "REALIZABLE_CANDIDATE"]

    proof_state = Dict(
        "proof_state" => "iteration_072_5_baker_interface",
        "T_min" => isempty(records) ? 0 : minimum(r.T for r in records),
        "T_max" => isempty(records) ? 0 : maximum(r.T for r in records),
        "words_generated" => length(records),
        "primitive_words" => count(r -> r.primitive, records),
        "classification_counts" => counts,
        "open_candidates" => length(open_candidates),
        "nontrivial_realizable_candidates" => length(nontriv_realizable),
        "theorem_modules_enabled" =>
            apply_baker ? ["verified_bound", "oddstep_bound"] : String[],
        "theorem_config" => Dict(
            "verified_bound" => string(cfg.verified_bound),
            "oddstep_bound_enabled" => cfg.oddstep_bound_enabled,
            "oddstep_min_m_nontrivial" => cfg.oddstep_min_m_nontrivial,
            "oddstep_source" => cfg.oddstep_source,
            "oddstep_version" => cfg.oddstep_version,
        ),
    )

    if output_path !== nothing
        mkpath(dirname(output_path))
        out = Dict(
            "proof_state" => proof_state,
            "rows" => rows,
            "open_candidates" => open_candidates,
        )
        open(output_path, "w") do io
            JSON.print(io, out, 2)
        end
    end

    return proof_state, rows, open_candidates
end
