using JSON

struct PeriodicRecord
    word_bits::String
    T::Int
    m::Int
    S::Int
    A::BigInt
    B::BigInt
    denom::BigInt
    primitive::Bool
    cyclic_admissible::Bool
    canonical_rotation::String
    rotation_index::Int
end

function parse_periodic(obj::Dict)
    return PeriodicRecord(
        String(obj["word_bits"]),
        Int(obj["T"]),
        Int(obj["m"]),
        Int(obj["S"]),
        parse(BigInt, String(obj["A_str"])),
        parse(BigInt, String(obj["B_str"])),
        parse(BigInt, String(obj["denom_str"])),
        Bool(obj["primitive"]),
        Bool(obj["cyclic_admissible"]),
        String(obj["canonical_rotation"]),
        Int(obj["rotation_index"]),
    )
end

function read_periodic_ndjson(path::AbstractString)::Vector{PeriodicRecord}
    out = PeriodicRecord[]
    open(path, "r") do io
        for line in eachline(io)
            line = strip(line)
            if isempty(line); continue; end
            push!(out, parse_periodic(JSON.parse(line)))
        end
    end
    return out
end
