struct ClassificationResult
    classification::String
    n_candidate::Union{Nothing, BigInt}
    notes::String
end

function bits_to_vec(word_bits::AbstractString)::Vector{Int}
    return [c == '1' ? 1 : 0 for c in collect(word_bits)]
end

"""
    simulate_period_word(n::BigInt, bits::Vector{Int})

Simulate one period of `bits` from positive integer `n`. Returns
`(parity_match::Bool, final_n::BigInt)` where parity_match indicates
whether each step's actual parity matched the prescribed bit.
"""
function simulate_period_word(n::BigInt, bits::Vector{Int})
    x = n
    for b in bits
        actual = isodd(x) ? 1 : 0
        if actual != b
            return (false, x)
        end
        if b == 1
            x = 3*x + 1
        else
            x = x ÷ 2
        end
    end
    return (true, x)
end

"""
    verify_collatz_cycle_periodic(n::BigInt, word_bits::AbstractString) -> Bool

True iff one period of `word_bits` from `n` (a) matches each step's
parity exactly and (b) returns to `n`.
"""
function verify_collatz_cycle_periodic(n::BigInt, word_bits::AbstractString)::Bool
    bits = bits_to_vec(word_bits)
    ok, x = simulate_period_word(n, bits)
    return ok && x == n
end

is_trivial_cycle_member(n::BigInt) = (n == 1 || n == 2 || n == 4)

function classify_fixed_point_periodic(rec::PeriodicRecord)::ClassificationResult
    denom = rec.denom
    B = rec.B
    if denom <= 0
        return ClassificationResult("NEGATIVE_OR_ZERO_DENOM", nothing, "denom <= 0")
    end
    if mod(B, denom) != 0
        return ClassificationResult("NON_INTEGER_FIXED_POINT", nothing, "B % denom != 0")
    end
    n = B ÷ denom
    if n <= 0
        return ClassificationResult("NON_POSITIVE_FIXED_POINT", nothing, "n <= 0")
    end
    if verify_collatz_cycle_periodic(n, rec.word_bits)
        if is_trivial_cycle_member(n)
            return ClassificationResult("REALIZABLE_TRIVIAL", n, "member of 1-2-4 cycle")
        else
            return ClassificationResult("REALIZABLE_CANDIDATE", n,
                                        "non-trivial positive integer fixed point")
        end
    end
    # Integer fixed point but parity simulation diverges -- means n is the
    # algebraic fixed point of the affine map but does not produce the
    # prescribed parity sequence, so does not realise this cycle.
    return ClassificationResult(
        "OPEN_CANDIDATE", n,
        "integer fixed point exists but parity simulation does not return to n"
    )
end
