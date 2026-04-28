"""
Iteration 072.5 candidate export.

Filters pipeline rows to those with `classification == "OPEN_CANDIDATE"`
and writes them to NDJSON / pretty JSON for downstream Baker modules.
"""

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

"""
    candidate_row_to_export_dict(row) -> Dict

Normalize a pipeline row into the export schema for downstream stages.
"""
function candidate_row_to_export_dict(row::Dict)
    return Dict(
        "word_bits" => row["word_bits"],
        "canonical_rotation" => row["canonical_rotation"],
        "T" => row["T"],
        "m" => row["m"],
        "S" => row["S"],
        "n_candidate_str" => get(row, "n_candidate_str", nothing),
        "baker_verdict" => get(row, "baker_verdict", nothing),
        "notes" => get(row, "notes", ""),
    )
end

"""
    export_open_candidates_ndjson(rows, path) -> Int

Write only OPEN_CANDIDATE rows to NDJSON. Returns the number written.
"""
function export_open_candidates_ndjson(rows::AbstractVector, path::AbstractString)::Int
    count = 0
    mkpath(dirname(path))
    open(path, "w") do io
        for row in rows
            if get(row, "classification", "") == "OPEN_CANDIDATE"
                JSON.print(io, candidate_row_to_export_dict(row))
                write(io, '\n')
                count += 1
            end
        end
    end
    return count
end

"""
    export_open_candidates_json(rows, path) -> Int

Pretty-write all OPEN_CANDIDATE rows + metadata to a single JSON file.
Returns the number written.
"""
function export_open_candidates_json(rows::AbstractVector, path::AbstractString)::Int
    out = Any[]
    for row in rows
        if get(row, "classification", "") == "OPEN_CANDIDATE"
            push!(out, candidate_row_to_export_dict(row))
        end
    end
    payload = Dict(
        "export_type" => "open_candidates",
        "count" => length(out),
        "candidates" => out,
    )
    mkpath(dirname(path))
    open(path, "w") do io
        JSON.print(io, payload, 2)
    end
    return length(out)
end
