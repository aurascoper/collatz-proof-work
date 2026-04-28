# Collatz Autoresearch Program

You are an autonomous proof-engineering agent working on the ordinary Collatz map.

You are NOT allowed to claim that the Collatz conjecture is proven unless all of the following pass:
1. A closed symbolic transition graph is generated.
2. The LP/certificate is feasible on the closed graph.
3. Exact rational verification passes on every closed constraint.
4. A written theorem statement specifies exactly what is proven.

## Current proof-state

- Ordinary Collatz drift is:
    `drift = m * (1 + log2(3)) - K`
  not `m * log2(3) - K`.
- Adjacent odd parity bits are impossible.
- Iteration 057 correctly enumerated admissible length-36 parity words:
    39,088,169 = F_38.
- Iteration 058b proved the closed parity-word overlap proxy graph is infeasible.
  This is only a parity-overlap abstraction, not the true affine residue graph.
- K=6 affine harness passed exactly.
- K=8 closed affine graph LP (060a) was infeasible under c_max aggregation.
- Iteration 060b extracted a K=8 witness with:
    `cycle_total_drift = -6.150374992788439`
    `cycle_total_depth_effect = +13`
    `integer_realizable_single_orbit = False`
  This suggests over-aggregation of c_max / incompatible depth-shift stitching.

## Primary overnight objective

Implement and run **Iteration 060c**.

### Iteration 060c

- K = 8.
- Build the closed affine residue-aware graph.
- Group transition constraints by `(E1, E2, c_val)`, not by `(E1, E2)` with independent c_max.
- Avoid taking a worst-case c_max over mutually incompatible fibers.
- Drift uses `pi_middle = pi_1` (the window between E1 and E2):
    `d = popcount(pi_1) * (1 + log2(3)) - K`
- Solve the robust LP with:
    zero objective,
    anchored `psi[0] = 0`,
    `lambda >= 0`.
- Report scipy `res.status` and `res.message`.
- If feasible:
    export certificate,
    run exact rational verifier using
    `LOG2_3_UPPER = Fraction(1584962500721157, 10**15)`.
- If infeasible:
    extract a cycle witness and report:
      `cycle_length`,
      `cycle_total_drift`,
      `cycle_total_depth_effect`,
      `integer_realizable_single_orbit`,
      `cycle_edges`,
      whether the obstruction is likely real or abstraction stitching.

## Hard rules

1. Every experiment must emit JSON proof_state to `proof_states/`.
2. Every infeasible LP must extract a witness cycle.
3. Every feasible LP must run a verifier or explain why verification is not yet possible.
4. Do not edit `CollatzConjecture(1).ipynb` directly. Work on the working copy or in `experiments/*.py`.
5. Use git. Commit only working experiments and include the proof_state file.
6. Never treat sampled results as universal.
7. Never use popcount differences as affine-cylinder depth shifts unless explicitly labeled as a proxy.
8. Use direct simulation sanity checks for affine boundary residues.
9. Keep runtime per experiment reasonable. Start K=6/K=8 before K=10/K=12.

## Scoring

A run is better if, in this order:
1. It finds a concrete modeling bug and fixes it.
2. It produces a smaller exact witness cycle.
3. It turns a sampled claim into a closed symbolic claim.
4. It verifies a certificate exactly.
5. It reduces abstraction artifacts.
6. It documents a hard negative result cleanly.

At the end of each run:
- Write `proof_states/iteration_XXX.json`.
- Append a short note to `README.md`.
- Commit if the run is valid and reproducible.
