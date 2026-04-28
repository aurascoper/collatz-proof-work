using Test
include("../src/CEEJulia.jl")
using .CEEJulia

@testset "Trivial cycle K=3 mask 0b001 (1->4->2->1)" begin
    # mask_le bit 0 = 1 (step 0 odd), bit 1 = 0 (step 1 even), bit 2 = 0
    # In LE encoding mask = 0b001 = 1
    pb = CEEJulia.ParityBlock(
        UInt64(1), 3, 1, 2,
        BigInt(3), BigInt(1), BigInt(3) - BigInt(3) + BigInt(0)
    )
    # Recompute denom = 2^S - A = 2^2 - 3^1 = 4 - 3 = 1
    pb = CEEJulia.ParityBlock(
        UInt64(1), 3, 1, 2,
        BigInt(3), BigInt(1), BigInt(1)
    )
    cls, n = classify_fixed_point(pb)
    @test cls == CEEJulia.REALIZABLE_TRIVIAL
    @test n == 1
    cls2, info = verify_collatz_cycle(pb, n)
    @test cls2 == CEEJulia.REALIZABLE_TRIVIAL
    @test info["verified"]
end

@testset "K=8 alternating self-loop is artefact" begin
    # mask_le = 0x55 = 01010101 (bit 0 = 1)
    pb = CEEJulia.ParityBlock(
        UInt64(0x55), 8, 4, 4,
        BigInt(81), BigInt(65), BigInt(-65)
    )
    cls, n = classify_fixed_point(pb)
    @test cls == CEEJulia.NEGATIVE_OR_ZERO_DENOM
    @test n === nothing
end

@testset "Read NDJSON from Rust output" begin
    # The Rust crate emitted /tmp/cee_k12.ndjson; reuse if present.
    path = "/tmp/cee_k12.ndjson"
    if isfile(path)
        blocks = read_ndjson(path)
        @test length(blocks) == 377  # F_14
        # Run the pipeline on K=12 blocks
        result = run_pipeline(blocks)
        @info "K=12 pipeline counts" result.counts
        # The only realizable cycles at K=12 are rotations of the
        # trivial 1-2-4 cycle (n in {1, 2, 4}); no other n is allowed.
        # If anything outside {1, 2, 4} appears, that's a non-trivial
        # Collatz cycle witness and warrants the highest alert.
        for w in result.realizable_witnesses
            @test w.n in (BigInt(1), BigInt(2), BigInt(4))
            if !(w.n in (BigInt(1), BigInt(2), BigInt(4)))
                @info "ALERT: candidate non-trivial Collatz cycle" w
            end
        end
    end
end

@testset "Baker bound returns positive values" begin
    @test baker_lower_bound(3, 5) > 0
    @test baker_lower_bound(100, 100) > 0
    @test baker_lower_bound(100, 100) < baker_lower_bound(3, 5)
end
