"""
    BakerVerdict

Result of an attempt to exclude a candidate cycle via an explicit
linear-forms-in-logarithms (Baker / Hercher / Mignotte / Laurent) bound
on `|m * log 3 - S * log 2|`.

`status` ∈ (:excluded, :not_excluded, :not_implemented).
"""
struct BakerVerdict
    status::Symbol
    lower_bound_expr::String
    theorem_source::String
    notes::String
end

"""
    apply_baker_bound(m::Int, S::Int, T::Int)::BakerVerdict

Iteration 072 SCAFFOLD: this records the high-precision numerical gap
`Δ = |m·log 3 - S·log 2|` for diagnostic purposes and returns
`:not_implemented`. Do NOT treat output as a rigorous bound.

A real implementation should plug in:
  - Hercher 2022 (arXiv:2201.00406) Section 3 explicit bound, OR
  - Laurent / Mignotte / Voutier explicit constants.

Both produce a lower bound of the form
    |m·log 3 - S·log 2| ≥ c(m, S) / max(m, S)^κ
for explicit `c, κ`. Iteration 072.5 will substitute one such theorem.
"""
function apply_baker_bound(m::Int, S::Int, T::Int)::BakerVerdict
    @assert m >= 0 && S >= 0 && T == m + S
    # High-precision numerical gap (only diagnostic)
    setprecision(BigFloat, 256) do
        gap = abs(m * log(big(3)) - S * log(big(2)))
        return BakerVerdict(
            :not_implemented,
            string(gap),
            "scaffold_only_use_Hercher_2022_or_Laurent_Mignotte",
            "high-precision diagnostic only; not a rigorous lower bound"
        )
    end
end
