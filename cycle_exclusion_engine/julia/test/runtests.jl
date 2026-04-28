using Test
include("../src/CEEJulia.jl")
using .CEEJulia

@testset "Trivial cycle K=3 mask 0b001 (1->4->2->1) — old single-block API" begin
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

@testset "Iteration 072 periodic record + classifier" begin
    # Trivial T=3 cycle in canonical form "001" (MSB-first, time
    # order [0, 0, 1]). Canonical recurrence gives A=3, B=4, S=2,
    # denom=1, n = B/denom = 4. The orbit is 4 -> 2 -> 1 -> 4.
    rec = CEEJulia.PeriodicRecord(
        "001", 3, 1, 2,
        BigInt(3), BigInt(4), BigInt(1),
        true, true, "001", 0,
    )
    res = CEEJulia.classify_fixed_point_periodic(rec)
    @test res.classification == "REALIZABLE_TRIVIAL"
    @test res.n_candidate == 4
    @test verify_collatz_cycle_periodic(BigInt(4), "001")
end

@testset "Iteration 072 K=8 alternating self-loop is NEGATIVE_OR_ZERO_DENOM" begin
    rec = CEEJulia.PeriodicRecord(
        "10101010", 8, 4, 4,
        BigInt(81), BigInt(65), BigInt(-65),
        true, true, "00101010", 1,  # canonical rotation
    )
    res = CEEJulia.classify_fixed_point_periodic(rec)
    @test res.classification == "NEGATIVE_OR_ZERO_DENOM"
    @test res.n_candidate === nothing
end

@testset "Pipeline end-to-end on T<=12 NDJSON from Rust" begin
    path = "/tmp/periodic_T12.ndjson"
    if isfile(path)
        ps, rows = run_periodic_pipeline(path; verified_bound=big(2)^68)
        @test ps["nontrivial_realizable_candidates"] == 0
        # Exactly one trivial cycle representative survives
        n_trivial = ps["classification_counts"]["REALIZABLE_TRIVIAL"]
        @test n_trivial == 1
        # No open candidates or finite-verification escapes at T<=12
        @test ps["classification_counts"]["OPEN_CANDIDATE"] == 0
        @test ps["classification_counts"]["EXCLUDED_BY_FINITE_VERIFICATION"] == 0
    else
        @warn "T<=12 NDJSON not present; skipping pipeline test"
    end
end

@testset "Baker interface returns :not_implemented" begin
    v = apply_baker_bound(4, 4, 8)
    @test v.status == :not_implemented
    @test occursin("scaffold", v.theorem_source)
end
