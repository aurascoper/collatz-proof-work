"""
Iteration 072.6 -- candidate analyzer.

For each OPEN_CANDIDATE row, compute high-precision diagnostics:
  - Δ = |m·log 3 − S·log 2|  (the linear form whose smallness signals
                              proximity to the dangerous resonance
                              3^m ≈ 2^S),
  - ratio_gap = |S/m − log_2 3|,
  - nearest continued-fraction convergent of log_2(3),
  - hardness_score = 1 / (Δ + 1e-50).

Smaller Δ ⇒ candidate is closer to the resonance, hence harder to
exclude by any Baker-class linear-forms-in-logarithms bound.
"""

struct AnalyzerConfig
    precision_bits::Int
    shortlist_size::Int
end

function default_analyzer_config()
    return AnalyzerConfig(512, 50)
end

"""
    parse_bigfloat_logs(cfg) -> (log2v, log3v, ratio)

Return high-precision log(2), log(3), and ratio = log(3)/log(2).
"""
function parse_bigfloat_logs(cfg::AnalyzerConfig)
    return setprecision(cfg.precision_bits) do
        log2v = log(big(2))
        log3v = log(big(3))
        return log2v, log3v, log3v / log2v
    end
end

"""
    cf_convergents(x, max_terms) -> Vector{Tuple{BigInt, BigInt, BigFloat}}

Compute simple continued-fraction convergents (p, q, p/q) of x.
"""
function cf_convergents(x::BigFloat, max_terms::Int = 32)
    terms = Int[]
    y = x
    for _ in 1:max_terms
        a = floor(BigInt, y)
        push!(terms, Int(a))  # a fits if input is bounded; safe for log(3)/log(2) ~ 1.585
        frac = y - BigFloat(a)
        if frac == 0
            break
        end
        y = inv(frac)
    end
    convs = Tuple{BigInt, BigInt, BigFloat}[]
    pnm2, pnm1 = BigInt(0), BigInt(1)
    qnm2, qnm1 = BigInt(1), BigInt(0)
    for a in terms
        p = BigInt(a) * pnm1 + pnm2
        q = BigInt(a) * qnm1 + qnm2
        push!(convs, (p, q, BigFloat(p) / BigFloat(q)))
        pnm2, pnm1 = pnm1, p
        qnm2, qnm1 = qnm1, q
    end
    return convs
end

function nearest_convergent(target::BigFloat, convs)
    best = nothing
    besterr = nothing
    for (p, q, approx) in convs
        err = abs(target - approx)
        if best === nothing || err < besterr
            best = (p, q, approx)
            besterr = err
        end
    end
    return best, besterr
end

"""
    analyze_candidate(obj; cfg) -> Dict

Compute high-precision diagnostics for a single OPEN_CANDIDATE record.
"""
function analyze_candidate(obj::Dict; cfg::AnalyzerConfig = default_analyzer_config())
    m = Int(obj["m"])
    S = Int(obj["S"])
    T = Int(obj["T"])

    setprecision(BigFloat, cfg.precision_bits)
    log2v, log3v, ratio = parse_bigfloat_logs(cfg)
    delta = abs(BigFloat(m) * log3v - BigFloat(S) * log2v)
    ratio_gap = m > 0 ? abs(BigFloat(S) / BigFloat(m) - ratio) : BigFloat(0)
    convs = cf_convergents(ratio, 32)
    target = m > 0 ? BigFloat(S) / BigFloat(m) : BigFloat(0)
    nearest, nearest_err = nearest_convergent(target, convs)
    p, q, approx = nearest
    hardness = inv(delta + BigFloat(1e-50))

    return Dict(
        "word_bits" => obj["word_bits"],
        "canonical_rotation" => get(obj, "canonical_rotation", obj["word_bits"]),
        "T" => T,
        "m" => m,
        "S" => S,
        "n_candidate_str" => get(obj, "n_candidate_str", nothing),
        "delta_str" => string(delta),
        "ratio_gap_str" => string(ratio_gap),
        "nearest_cf_p" => string(p),
        "nearest_cf_q" => string(q),
        "nearest_cf_value_str" => string(approx),
        "nearest_cf_error_str" => string(nearest_err),
        "hardness_score_str" => string(hardness),
        "baker_verdict" => get(obj, "baker_verdict", nothing),
        "notes" => get(obj, "notes", ""),
    )
end

"""
    analyze_open_candidates_ndjson(path; cfg) -> Vector{Dict}

Read OPEN_CANDIDATE NDJSON, analyze, return rows sorted by ascending
delta (smallest first = hardest).
"""
function analyze_open_candidates_ndjson(path::AbstractString;
                                          cfg::AnalyzerConfig = default_analyzer_config())
    analyzed = Dict[]
    if !isfile(path)
        return analyzed
    end
    open(path, "r") do io
        for line in eachline(io)
            line = strip(line)
            if isempty(line); continue; end
            obj = JSON.parse(line)
            push!(analyzed, analyze_candidate(obj; cfg = cfg))
        end
    end
    # Sort by parsed BigFloat delta ascending
    sort!(analyzed,
          by = r -> parse(BigFloat, r["delta_str"]))
    return analyzed
end

"""
    export_ranked_candidates_json(rows, path; cfg) -> Int

Export ranked candidates plus a shortlist of size `cfg.shortlist_size`.
Returns the total number of analyzed rows.
"""
function export_ranked_candidates_json(rows::AbstractVector,
                                         path::AbstractString;
                                         cfg::AnalyzerConfig = default_analyzer_config())
    shortlist = rows[1:min(cfg.shortlist_size, length(rows))]
    payload = Dict(
        "proof_state" => "iteration_072_6_candidate_analyzer",
        "n_candidates" => length(rows),
        "precision_bits" => cfg.precision_bits,
        "shortlist_size" => length(shortlist),
        "ranking_metric" => "ascending delta = |m*log(3) - S*log(2)|",
        "rows" => rows,
        "shortlist" => shortlist,
    )
    mkpath(dirname(path))
    open(path, "w") do io
        JSON.print(io, payload, 2)
    end
    return length(rows)
end
