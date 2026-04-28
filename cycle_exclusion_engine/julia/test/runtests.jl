using Test
include("../src/CEEJulia.jl")
using .CEEJulia

@testset "Trivial cycle classification — periodic API" begin
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

@testset "K=8 alternating self-loop is NEGATIVE_OR_ZERO_DENOM" begin
    rec = CEEJulia.PeriodicRecord(
        "10101010", 8, 4, 4,
        BigInt(81), BigInt(65), BigInt(-65),
        true, true, "00101010", 1,
    )
    res = CEEJulia.classify_fixed_point_periodic(rec)
    @test res.classification == "NEGATIVE_OR_ZERO_DENOM"
end

@testset "Baker: verified bound excludes candidate below ceiling" begin
    cfg = default_theorem_config()
    inp = BakerInput(
        "001001", "001001", 6, 2, 4,
        big(9), big(70), big(7),
        big(10),
    )
    v = apply_verified_bound(inp; cfg = cfg)
    @test v.status == :excluded_by_verified_bound
end

@testset "Baker: oddstep excludes nontrivial low-m candidate" begin
    cfg = default_theorem_config()
    # n is large to bypass verified-bound; m well below 92.
    inp = BakerInput(
        "001001", "001001", 6, 2, 4,
        big(9), big(700), big(7),
        big(2)^70 + big(123),  # > verified bound
    )
    v = apply_oddstep_bound(inp; cfg = cfg)
    @test v.status == :excluded_by_theorem
end

@testset "Baker: trivial cycle pass-through" begin
    cfg = default_theorem_config()
    inp = BakerInput(
        "001", "001", 3, 1, 2,
        big(3), big(4), big(1), big(4),
    )
    v = apply_baker_bound(inp; cfg = cfg)
    @test v.status == :not_applicable
end

@testset "Baker: nothing candidate -> not_applicable" begin
    cfg = default_theorem_config()
    inp = BakerInput(
        "01", "01", 2, 1, 1,
        big(3), big(2), big(-1), nothing,
    )
    v = apply_baker_bound(inp; cfg = cfg)
    @test v.status == :not_applicable
end

@testset "Pipeline end-to-end on T<=12 NDJSON" begin
    path = "/tmp/periodic_T12.ndjson"
    if isfile(path)
        ps, rows, open_cands = run_periodic_pipeline(
            path; cfg = default_theorem_config(), apply_baker = true,
        )
        @test ps["nontrivial_realizable_candidates"] == 0
        @test ps["classification_counts"]["REALIZABLE_TRIVIAL"] == 1
        @test ps["classification_counts"]["OPEN_CANDIDATE"] == 0
        @test isempty(open_cands)
    end
end

@testset "Candidate export NDJSON filters OPEN_CANDIDATE only" begin
    rows = Dict[
        Dict("word_bits"=>"001", "canonical_rotation"=>"001",
             "T"=>3, "m"=>1, "S"=>2,
             "classification"=>"REALIZABLE_TRIVIAL",
             "n_candidate_str"=>"4", "notes"=>"trivial"),
        Dict("word_bits"=>"001001001", "canonical_rotation"=>"001001001",
             "T"=>9, "m"=>3, "S"=>6,
             "classification"=>"OPEN_CANDIDATE",
             "n_candidate_str"=>"123456789",
             "notes"=>"survives current theorem layer"),
    ]
    p = tempname() * ".ndjson"
    n = export_open_candidates_ndjson(rows, p)
    @test n == 1
    lines = readlines(p)
    @test length(lines) == 1
    @test occursin("001001001", lines[1])
end

@testset "Candidate analyzer basic diagnostics" begin
    obj = Dict(
        "word_bits" => "001001001",
        "canonical_rotation" => "001001001",
        "T" => 9, "m" => 3, "S" => 6,
        "n_candidate_str" => "123456789",
    )
    row = analyze_candidate(obj)
    @test haskey(row, "delta_str")
    @test haskey(row, "ratio_gap_str")
    @test haskey(row, "nearest_cf_p")
    @test haskey(row, "nearest_cf_q")
    @test parse(BigFloat, row["delta_str"]) >= 0
end
