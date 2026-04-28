using JSON

"""
    run_periodic_pipeline(ndjson_path; verified_bound, apply_baker, output_path)

Iteration 072 main entry. For each periodic record, classify the affine
fixed point, optionally invoke the verified-bound finite check
(`n <= verified_bound` -> direct Collatz simulation) and the Baker
bound interface.

Returns `(proof_state::Dict, rows::Vector{Dict})`.
"""
function run_periodic_pipeline(ndjson_path::AbstractString;
                                verified_bound::BigInt = big(2)^68,
                                apply_baker::Bool = false,
                                output_path::Union{Nothing, AbstractString} = nothing)
    records = read_periodic_ndjson(ndjson_path)

    counts = Dict(
        "NEGATIVE_OR_ZERO_DENOM" => 0,
        "NON_INTEGER_FIXED_POINT" => 0,
        "NON_POSITIVE_FIXED_POINT" => 0,
        "REALIZABLE_TRIVIAL" => 0,
        "REALIZABLE_CANDIDATE" => 0,
        "EXCLUDED_BY_FINITE_VERIFICATION" => 0,
        "EXCLUDED_BY_BAKER_BOUND" => 0,
        "OPEN_CANDIDATE" => 0,
    )

    rows = Dict[]
    open_candidates = String[]

    for rec in records
        result = classify_fixed_point_periodic(rec)
        cls = result.classification
        n = result.n_candidate
        baker_status = "not_used"

        # Stage 5: verified-bound finite verification (overrides
        # REALIZABLE_CANDIDATE iff n is small enough to simulate directly
        # using the global Collatz iteration -- not just one period).
        if cls == "REALIZABLE_CANDIDATE" && n !== nothing && n <= verified_bound
            # Run the global Collatz iteration starting from n. If it
            # reaches 1 in finitely many steps, `n` cannot be on a
            # non-trivial cycle (since cycles are recurrent). However,
            # a true *cycle* fixed point would not reach 1 -- it would
            # stay in the cycle. So if iteration reaches 1, this is
            # actually a contradiction with `verify_collatz_cycle_periodic`
            # returning true. Keep this check as a sanity layer.
            cls = "REALIZABLE_CANDIDATE"  # leave as candidate; the cycle
                                          # check has already passed.
            # The "EXCLUDED_BY_FINITE_VERIFICATION" is for OPEN_CANDIDATE
            # cases where the algebraic fixed point exists but the cycle
            # parity match fails; in that case n must descend to 1.
        end
        if cls == "OPEN_CANDIDATE" && n !== nothing && n <= verified_bound
            # Direct Collatz simulation from n: if it reaches 1 within a
            # bounded step count, classify as EXCLUDED_BY_FINITE_VERIFICATION.
            sim_n = n
            steps = 0
            max_steps = 10_000_000
            while sim_n != 1 && steps < max_steps
                if isodd(sim_n)
                    sim_n = 3*sim_n + 1
                else
                    sim_n = sim_n ÷ 2
                end
                steps += 1
            end
            if sim_n == 1
                cls = "EXCLUDED_BY_FINITE_VERIFICATION"
            end
        end

        # Stage 6: Baker-bound interface (scaffold; never sets :excluded)
        if cls == "REALIZABLE_CANDIDATE" && apply_baker
            verdict = apply_baker_bound(rec.m, rec.S, rec.T)
            baker_status = string(verdict.status)
            if verdict.status == :excluded
                cls = "EXCLUDED_BY_BAKER_BOUND"
            else
                push!(open_candidates, rec.word_bits)
            end
        elseif cls == "REALIZABLE_CANDIDATE"
            push!(open_candidates, rec.word_bits)
        end

        counts[cls] = get(counts, cls, 0) + 1

        push!(rows, Dict(
            "word_bits" => rec.word_bits,
            "canonical_rotation" => rec.canonical_rotation,
            "T" => rec.T,
            "m" => rec.m,
            "S" => rec.S,
            "classification" => cls,
            "n_candidate_str" => isnothing(n) ? nothing : string(n),
            "baker_status" => baker_status,
            "notes" => result.notes,
        ))
    end

    nontrivial_realizable = [r for r in rows
                              if r["classification"] == "REALIZABLE_CANDIDATE"]

    proof_state = Dict(
        "proof_state" => "iteration_072_periodic_cycle_engine",
        "T_min" => isempty(records) ? 0 : minimum(r.T for r in records),
        "T_max" => isempty(records) ? 0 : maximum(r.T for r in records),
        "words_generated" => length(records),
        "primitive_words" => count(r -> r.primitive, records),
        "classification_counts" => counts,
        "nontrivial_realizable_candidates" => length(nontrivial_realizable),
        "nontrivial_realizable_examples" => nontrivial_realizable[1:min(10, end)],
        "baker_interface_used" => apply_baker,
        "verified_bound_used" => string(verified_bound),
    )

    if output_path !== nothing
        out = Dict("proof_state" => proof_state, "rows" => rows)
        open(output_path, "w") do io
            JSON.print(io, out, 2)
        end
    end

    return proof_state, rows
end
