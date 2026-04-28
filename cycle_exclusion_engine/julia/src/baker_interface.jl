"""
Iteration 072.5 -- theorem-parameterized Baker exclusion interface.

The interface is RIGOROUS in the sense that every exclusion records its
theorem source. The actual exclusion theorems implemented here are:

  1. apply_verified_bound      -- trusted external finite verification
                                  ceiling (e.g. n <= 2^68 per Roosendaal).
  2. apply_oddstep_bound       -- explicit odd-step lower bound for
                                  non-trivial Collatz cycles
                                  (defaults to m >= 92 per Hercher 2022).

Open candidates that survive both layers are passed to the OPEN_CANDIDATE
queue for stronger downstream theorems (e.g. Baker / Laurent / Mignotte
linear-forms-in-logarithms bounds), implemented in future iterations.
"""

# ---- Input / verdict types ----

struct BakerInput
    word_bits::String
    canonical_rotation::String
    T::Int
    m::Int
    S::Int
    A::BigInt
    B::BigInt
    denom::BigInt
    n_candidate::Union{Nothing, BigInt}
end

struct BakerVerdict
    status::Symbol
    theorem_source::String
    theorem_version::String
    lower_bound_expr::String
    exclusion_reason::String
    numeric_gap_str::String
    threshold_data::Dict{String, String}
    notes::String
end

# Allowed status values (informational; not enforced):
#   :excluded_by_verified_bound
#   :excluded_by_theorem
#   :open_candidate
#   :not_applicable
#   :not_implemented

# ---- Theorem config ----

struct TheoremConfig
    verified_bound::BigInt
    oddstep_bound_enabled::Bool
    oddstep_min_m_nontrivial::Int
    oddstep_source::String
    oddstep_version::String
end

function default_theorem_config()
    return TheoremConfig(
        big(2)^68,                         # Roosendaal-class finite ceiling
        true,
        92,                                # Hercher 2022, m >= 92 for non-trivial cycle
        "Hercher 2022 (arXiv:2201.00406)",
        "odd-step lower bound for non-trivial Collatz cycles",
    )
end

# ---- Helpers ----

function _mkverdict(; status::Symbol,
                    theorem_source::String,
                    theorem_version::String,
                    lower_bound_expr::String = "",
                    exclusion_reason::String = "",
                    numeric_gap_str::String = "",
                    threshold_data::Dict{String,String} = Dict{String,String}(),
                    notes::String = "")
    return BakerVerdict(status, theorem_source, theorem_version,
                        lower_bound_expr, exclusion_reason,
                        numeric_gap_str, threshold_data, notes)
end

"""
    build_baker_input(rec::PeriodicRecord, result::ClassificationResult) -> BakerInput

Lift a classified periodic record into the theorem-exclusion interface.
"""
function build_baker_input(rec::PeriodicRecord, result::ClassificationResult)::BakerInput
    return BakerInput(
        rec.word_bits, rec.canonical_rotation, rec.T, rec.m, rec.S,
        rec.A, rec.B, rec.denom, result.n_candidate,
    )
end

# ---- Verified-bound exclusion ----

function apply_verified_bound(inp::BakerInput;
                              cfg::TheoremConfig = default_theorem_config())::BakerVerdict
    n = inp.n_candidate
    if n === nothing
        return _mkverdict(
            status = :not_applicable,
            theorem_source = "finite_verification",
            theorem_version = "trusted_external_bound",
            exclusion_reason = "No positive integer candidate",
            notes = "Candidate already excluded structurally before finite verification.",
        )
    end
    if n <= cfg.verified_bound
        return _mkverdict(
            status = :excluded_by_verified_bound,
            theorem_source = "finite_verification",
            theorem_version = "trusted_external_bound",
            lower_bound_expr = "n <= verified_bound",
            exclusion_reason = "Candidate lies below trusted verification ceiling",
            numeric_gap_str = string(cfg.verified_bound - n),
            threshold_data = Dict(
                "n_candidate" => string(n),
                "verified_bound" => string(cfg.verified_bound),
            ),
            notes = "Excluded by trusted external finite verification bound.",
        )
    end
    return _mkverdict(
        status = :open_candidate,
        theorem_source = "finite_verification",
        theorem_version = "trusted_external_bound",
        lower_bound_expr = "n <= verified_bound",
        exclusion_reason = "Candidate exceeds trusted verification ceiling",
        numeric_gap_str = string(n - cfg.verified_bound),
        threshold_data = Dict(
            "n_candidate" => string(n),
            "verified_bound" => string(cfg.verified_bound),
        ),
        notes = "Requires theorem-based exclusion beyond finite verification.",
    )
end

# ---- Odd-step exclusion (Hercher-class) ----

function apply_oddstep_bound(inp::BakerInput;
                             cfg::TheoremConfig = default_theorem_config())::BakerVerdict
    n = inp.n_candidate
    if !cfg.oddstep_bound_enabled
        return _mkverdict(
            status = :not_implemented,
            theorem_source = cfg.oddstep_source,
            theorem_version = cfg.oddstep_version,
            exclusion_reason = "Odd-step theorem disabled in config",
            notes = "No odd-step exclusion applied.",
        )
    end
    if n === nothing
        return _mkverdict(
            status = :not_applicable,
            theorem_source = cfg.oddstep_source,
            theorem_version = cfg.oddstep_version,
            exclusion_reason = "No positive integer candidate to test",
            notes = "Candidate already excluded structurally.",
        )
    end
    if n in (big(1), big(2), big(4))
        return _mkverdict(
            status = :not_applicable,
            theorem_source = cfg.oddstep_source,
            theorem_version = cfg.oddstep_version,
            exclusion_reason = "Trivial 1-2-4 cycle not targeted",
            threshold_data = Dict("n_candidate" => string(n)),
            notes = "The theorem excludes non-trivial cycles only.",
        )
    end
    if inp.m < cfg.oddstep_min_m_nontrivial
        return _mkverdict(
            status = :excluded_by_theorem,
            theorem_source = cfg.oddstep_source,
            theorem_version = cfg.oddstep_version,
            lower_bound_expr = "non-trivial cycles require m >= $(cfg.oddstep_min_m_nontrivial)",
            exclusion_reason = "Candidate has too few odd steps",
            numeric_gap_str = string(cfg.oddstep_min_m_nontrivial - inp.m),
            threshold_data = Dict(
                "m" => string(inp.m),
                "required_min_m" => string(cfg.oddstep_min_m_nontrivial),
            ),
            notes = "Excluded by explicit odd-step lower bound.",
        )
    end
    return _mkverdict(
        status = :open_candidate,
        theorem_source = cfg.oddstep_source,
        theorem_version = cfg.oddstep_version,
        lower_bound_expr = "non-trivial cycles require m >= $(cfg.oddstep_min_m_nontrivial)",
        exclusion_reason = "Candidate exceeds odd-step theorem threshold",
        numeric_gap_str = string(inp.m - (cfg.oddstep_min_m_nontrivial - 1)),
        threshold_data = Dict(
            "m" => string(inp.m),
            "required_min_m" => string(cfg.oddstep_min_m_nontrivial),
        ),
        notes = "Not excluded by this theorem alone.",
    )
end

# ---- Master dispatcher ----

"""
    apply_baker_bound(inp::BakerInput; cfg) -> BakerVerdict

Theorem-dispatch policy:
  1. structural exclusions already handled before this layer
  2. trivial cycle pass-through
  3. trusted finite verification
  4. odd-step lower bound
  5. else OPEN_CANDIDATE
"""
function apply_baker_bound(inp::BakerInput;
                           cfg::TheoremConfig = default_theorem_config())::BakerVerdict
    n = inp.n_candidate
    if n === nothing
        return _mkverdict(
            status = :not_applicable,
            theorem_source = "structural",
            theorem_version = "exact_fixed_point_classifier",
            exclusion_reason = "No positive integer candidate",
            notes = "Filtered before theorem layer.",
        )
    end
    if n in (big(1), big(2), big(4))
        return _mkverdict(
            status = :not_applicable,
            theorem_source = "trivial_cycle",
            theorem_version = "exact_fixed_point_classifier",
            exclusion_reason = "Trivial 1-2-4 cycle representative",
            threshold_data = Dict("n_candidate" => string(n)),
            notes = "Not a non-trivial cycle candidate.",
        )
    end
    vbound = apply_verified_bound(inp; cfg = cfg)
    if vbound.status == :excluded_by_verified_bound
        return vbound
    end
    oddstep = apply_oddstep_bound(inp; cfg = cfg)
    if oddstep.status == :excluded_by_theorem
        return oddstep
    end
    return _mkverdict(
        status = :open_candidate,
        theorem_source = "composite",
        theorem_version = "finite_bound + oddstep_bound",
        exclusion_reason = "Survives currently implemented theorem layers",
        threshold_data = Dict(
            "m" => string(inp.m),
            "S" => string(inp.S),
            "n_candidate" => string(inp.n_candidate),
        ),
        notes = "Pass to stronger logarithmic-forms / Baker module.",
    )
end
