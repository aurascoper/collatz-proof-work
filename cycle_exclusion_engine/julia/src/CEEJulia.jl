module CEEJulia

using JSON

# Iteration 072 additions
include("periodic_reader.jl")
include("exact_classifier_periodic.jl")
include("baker_interface.jl")
include("pipeline_periodic.jl")

export PeriodicRecord, ClassificationResult, BakerVerdict
export read_periodic_ndjson, classify_fixed_point_periodic,
       verify_collatz_cycle_periodic, apply_baker_bound,
       run_periodic_pipeline

export ParityBlock, classify_fixed_point, verify_collatz_cycle,
       baker_lower_bound, read_ndjson, run_pipeline,
       Classification

# ---------------------------------------------------------------------------
# Parity block reader
# ---------------------------------------------------------------------------

struct ParityBlock
    mask_le::UInt64
    K::Int
    m::Int
    S::Int
    A::BigInt
    B::BigInt
    denom::BigInt
end

function ParityBlock(rec::Dict)
    mask = parse(UInt64, rec["mask_le_hex"][3:end], base=16)
    return ParityBlock(
        mask,
        rec["K"], rec["m"], rec["S"],
        parse(BigInt, rec["A_dec"]),
        parse(BigInt, rec["B_dec"]),
        parse(BigInt, rec["denom_dec"]),
    )
end

function read_ndjson(path::AbstractString)::Vector{ParityBlock}
    blocks = ParityBlock[]
    open(path, "r") do io
        for line in eachline(io)
            line = strip(line)
            if isempty(line)
                continue
            end
            push!(blocks, ParityBlock(JSON.parse(line)))
        end
    end
    return blocks
end

# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

@enum Classification begin
    NEGATIVE_OR_ZERO_DENOM       # denom <= 0 -> structurally non-realizable
    NON_INTEGER_FIXED_POINT      # denom > 0 but B mod denom != 0
    NON_POSITIVE_FIXED_POINT     # n_candidate <= 0
    REALIZABLE_TRIVIAL           # n_candidate = 1 (the trivial 1-2-4 cycle)
    REALIZABLE_CANDIDATE         # n_candidate > 1, integer -> needs full audit
    SIMULATION_PARITY_MISMATCH   # candidate fails direct simulation parity check
    SIMULATION_NOT_RETURN        # candidate doesn't return to n
end

"""
    classify_fixed_point(pb::ParityBlock) -> (cls::Classification, n::Union{BigInt, Nothing})

Pipeline step 3 of the Cycle Exclusion Engine: solve the affine fixed
point and classify. Does NOT run the BigInt verifier; that is step 5.
"""
function classify_fixed_point(pb::ParityBlock)
    if pb.denom <= 0
        return (NEGATIVE_OR_ZERO_DENOM, nothing)
    end
    q, r = divrem(pb.B, pb.denom)
    if r != 0
        return (NON_INTEGER_FIXED_POINT, nothing)
    end
    n = q  # = B / denom
    if n <= 0
        return (NON_POSITIVE_FIXED_POINT, nothing)
    elseif n == 1
        return (REALIZABLE_TRIVIAL, n)
    else
        return (REALIZABLE_CANDIDATE, n)
    end
end

# ---------------------------------------------------------------------------
# Arbitrary-precision verifier
# ---------------------------------------------------------------------------

"""
    verify_collatz_cycle(pb::ParityBlock, n::BigInt) -> (cls::Classification, info::Dict)

Pipeline step 5: simulate Collatz from `n` for K steps and verify:
  (a) parity at each step matches `pb.mask_le` (bit i = step i),
  (b) final value equals `n` (closing into a cycle).

If `n` is the trivial 1, this confirms the standard 1-2-4 cycle for
parity 100 (m=1, S=2). For any other `n`, this would be a
non-trivial cycle witness -- raise the highest possible alert.
"""
function verify_collatz_cycle(pb::ParityBlock, n::BigInt)
    cur = n
    bits = Int[]
    for i in 0:(pb.K - 1)
        b = Int(cur & 1)
        push!(bits, b)
        expected = Int((pb.mask_le >> i) & 1)
        if b != expected
            return (SIMULATION_PARITY_MISMATCH,
                    Dict("step"=>i, "expected"=>expected, "actual"=>b,
                         "value"=>string(cur)))
        end
        cur = b == 1 ? 3 * cur + 1 : cur >> 1
    end
    if cur != n
        return (SIMULATION_NOT_RETURN,
                Dict("final"=>string(cur), "expected"=>string(n)))
    end
    cls = n == 1 ? REALIZABLE_TRIVIAL : REALIZABLE_CANDIDATE
    return (cls, Dict("verified"=>true, "n"=>string(n), "bits"=>bits))
end

# ---------------------------------------------------------------------------
# Baker-bound interface (placeholder)
# ---------------------------------------------------------------------------

"""
    baker_lower_bound(m::Int, S::Int) -> Float64

Placeholder for an explicit Baker bound on `|m * log 3 - S * log 2|`.
The actual rigorous form (Laurent / Mignotte / de Bruijn constants) is
out of scope for this prototype; this returns a coarse heuristic
so we can wire the pipeline. See Hercher 2022 (arXiv:2201.00406) for
a worked example of an explicit bound.
"""
function baker_lower_bound(m::Int, S::Int)::Float64
    # Heuristic: c / max(m, S)^kappa with c = 0.1, kappa = 13.3 (the
    # latter is roughly the order of magnitude in Hercher's setup for
    # admissible cycle lengths). Replace with a verified bound before
    # any rigorous use.
    @assert m >= 1 && S >= 1
    c = 0.1
    kappa = 13.3
    return c / (max(m, S))^kappa
end

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

"""
    run_pipeline(blocks::Vector{ParityBlock}; verify_threshold::BigInt = BigInt(2)^68)

Run the full classification pipeline on a list of parity blocks and
return aggregated counts plus any `REALIZABLE_CANDIDATE` (non-trivial)
witnesses for further inspection.
"""
function run_pipeline(blocks::Vector{ParityBlock};
                     verify_threshold::BigInt = BigInt(2)^68)
    counts = Dict{Classification, Int}()
    realizable_witnesses = []
    candidate_n_values = BigInt[]
    for pb in blocks
        (cls, n) = classify_fixed_point(pb)
        if cls == REALIZABLE_TRIVIAL || cls == REALIZABLE_CANDIDATE
            (cls2, info) = verify_collatz_cycle(pb, n::BigInt)
            cls = cls2
            if cls == REALIZABLE_CANDIDATE
                push!(realizable_witnesses, (mask_le=pb.mask_le, K=pb.K,
                                             m=pb.m, S=pb.S, n=n, info=info))
            end
            push!(candidate_n_values, n)
        end
        counts[cls] = get(counts, cls, 0) + 1
    end
    return (counts=counts,
            realizable_witnesses=realizable_witnesses,
            candidate_n_values=candidate_n_values)
end

end # module
