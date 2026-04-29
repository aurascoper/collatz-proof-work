# collatz-proof-work

> **Closed-graph cycle-negativity at $K = 8$ and primitive periodic-word
> exclusion through $T \le 36$ for the ordinary Collatz map: two
> computational artefacts.**

[![status](https://img.shields.io/badge/status-preprint--ready-brightgreen)](https://github.com/aurascoper/collatz-proof-work/releases/tag/preprint-ready-2026-04-28)
[![claim discipline](https://img.shields.io/badge/claim%20discipline-green-success)](EDITORIAL_REVIEW_2026-04-28.md)
[![not a Collatz proof](https://img.shields.io/badge/not%20a%20Collatz%20proof-yellow)](#limitations-and-non-claims)
[![code license](https://img.shields.io/badge/code-MIT-blue)](LICENSE-CODE)
[![docs license](https://img.shields.io/badge/docs-CC--BY--4.0-blue)](LICENSE-DOCS)

This repository contains **two distinct computational artefacts** on
the ordinary Collatz map $T : \mathbb{Z}_{>0} \to \mathbb{Z}_{>0}$,
defined by

$$
T(n) \;=\; \begin{cases} 3n + 1 & \text{if } n \text{ is odd},\\[2pt] n / 2 & \text{if } n \text{ is even}. \end{cases}
$$

Both artefacts are presented under strict claim discipline. **Neither is a proof of the Collatz
conjecture.** This is documented engineering and computational verification,
not a closed mathematical resolution; the strongest results here are strictly
weaker than the literature already cited
([Hercher 2022](https://arxiv.org/abs/2201.00406);
[Tao 2019](https://arxiv.org/abs/1909.03562)).

---

## Abstract

Let $\pi = (b_0, b_1, \dots, b_{T-1}) \in \{0,1\}^T$ be the parity
vector of an integer $n$ over $T$ steps of the ordinary Collatz map.
For ordinary Collatz the constraint $b_i = 1 \Rightarrow b_{i+1} = 0$
holds (the no-adjacent-ones rule). Composing the Collatz step in
time order via the canonical recurrence

$$
\begin{aligned}
A_0 = 1,\; B_0 = 0,\; S_0 = 0; \qquad
\text{for each } b_i\;:\;\;
&\text{if } b_i = 1 \;:\; B \mapsto 3B + 2^S,\;\; A \mapsto 3A,\\
&\text{if } b_i = 0 \;:\; S \mapsto S + 1
\end{aligned}
$$

yields $A = 3^m$ (with $m$ the number of odd steps), $S = T - m$, and an
affine map

$$
T_\pi(n) \;=\; \frac{A\,n + B}{2^S},
$$

with the cycle-fixed-point equation $(2^S - 3^m)\, n \;=\; B$.

### Branch I — closed-graph LP at $K = 8$

We exhibit, on the closed 2-window edge-state graph at $K = 8$
(535,168 states; 12,711,807 edges, with edges realised by integers in
$[1,\,2^{3K})$), a difference potential $\psi : \mathrm{States} \to
\mathbb{Q}$ such that for every edge $e = (E_1, E_2)$,

$$
\psi(E_2) - \psi(E_1) - \lambda \cdot S(e) \;\le\; -\,\mathrm{drift}(e) - \varepsilon,
$$

with the parity-induced constant

$$
\lambda \;=\; \mathrm{LOG2\_3\_UPPER} - 1 + 10^{-6},
\qquad
\mathrm{LOG2\_3\_UPPER} \;=\; \tfrac{1\,584\,962\,500\,721\,157}{10^{15}},
$$

drift $\mathrm{drift}(e) = m_{\mathrm{middle}}(1 + \log_2 3) - K$, and
$S(e) = K - m_{\mathrm{middle}}$. The certificate is verified
exactly in $\mathbb{Q}$ on every one of the 12,711,807 edges
(Iteration 069a; **0/12,711,807 failures**). By LP duality, every
directed cycle in the *reweighted* abstract graph has total weight
$\le -|C|\cdot\varepsilon$. We refer to this as a **closed-graph
cycle-negativity certificate**; it is *not* a Lyapunov descent
statement on positive-integer trajectories — see §[Negative findings](#negative-findings-built-in).

### Branch II — primitive periodic-word exclusion engine

A two-language pipeline (Rust generator + Julia exact classifier
with a theorem dispatcher) enumerates every primitive cyclically-
admissible periodic parity word of bounded length $T$, composes its
exact `BigInt` affine map, classifies the algebraic fixed point, and
dispatches surviving candidates through a theorem layer importing
[Hercher 2022](https://arxiv.org/abs/2201.00406)'s
$m \ge 92$ lower bound and a trusted finite-verification ceiling.
Through $T \le 36$ (**2,552,323 primitive words**, 327 s end-to-end),
the engine produces **exactly one realisable class** — the trivial
$1 \to 4 \to 2 \to 1$ cycle, canonical word `"001"`, $n = 4$ — and
**zero non-trivial or open candidates**.

A $T \le 48$ attempt is **disk-limited; deferred** (NDJSON transport
reached ~6.4 GB before completing, an engineering limit, not a
mathematical one).

---

## Strongest defensible claims

> **Claim A** (Branch I). On the closed $K = 8$ 2-window edge-state
> graph (12,711,807 edges, with edges realised by integers in
> $[1, 2^{3K})$), there exists $\psi : \mathrm{States} \to \mathbb{Q}$
> satisfying $\psi(E_2) - \psi(E_1) - \lambda \cdot S(e) \le
> -\mathrm{drift}(e) - \varepsilon$ for every edge $e$, with $\lambda$
> as above. Equivalently, by LP duality, every directed cycle in the
> *reweighted* abstract graph has total weight $\le -|C|\cdot\varepsilon$.
> **Status: EXACT** (Iteration 069a, 0 failures over 12,711,807
> constraints under exact $\mathbb{Q}$ arithmetic).
>
> **Claim B** (Branch II). For every primitive cyclically-admissible
> periodic parity word of length $T \le 36$, the engine produces
> exactly one realisable class — the trivial $1{-}4{-}2$ cycle in
> canonical form `"001"`, $n = 4$ — and zero non-trivial or open
> candidates. **Status: EXACT** (Iteration 073; 2,552,323 primitive
> words; in the scanned range only).

Both claims are reproductions of corollaries of the cited literature
(Branch I is strictly weaker than the LP-side literature; Branch II
is weaker than [Hercher 2022](https://arxiv.org/abs/2201.00406)'s
$m \le 91$ exclusion). The contribution is the auditable infrastructure,
not the underlying mathematical fact.

---

## Negative findings (built-in)

These results are part of the work, not footnotes.

1. **Iteration 069b — semantic-gap audit.** The cycle-level credit
   $-\lambda \cdot S(e)$ in the Branch I certificate is *worst-case backed*
   by an actual per-edge fuel drop on only **5.8 %** of edges at $K = 6$
   and **2.3 %** of edges at $K = 8$. The certificate is a difference
   potential, not a Lyapunov.
2. **Iteration 071B — realised-trajectory infeasibility.** Replacing
   formula drift by worst-case actual drift gives excess
   $\log_2(1 + B_\pi / (3^m n))$ up to $\approx 0.83$ at $K=6$ and
   $\approx 1.245$ at $K=8$. The resulting LP is **infeasible** (proven
   at $K=6$; same mechanism at $K=8$). The fixed-$\lambda$ certificate
   is therefore *asymptotic* / large-$n$, not Lyapunov-on-integers.
3. **Iteration 075 — engineering wall at $T \le 48$.** The NDJSON
   pipeline reached ~6.4 GB before completing; the run was aborted
   to avoid disk exhaustion. **Disk-limited; deferred.** Not a
   mathematical outcome.

---

## Repository layout

```
.
├── notebook + LP-side experiments  (Iterations 057–071)
│   ├── CollatzConjecture_working.ipynb
│   ├── experiments/iteration_*.py
│   ├── verifiers/cycle_classifier.py
│   ├── verifiers/positivity_theorem.py
│   ├── verifiers/positivity_fuel.py
│   └── verifiers/verify_certificate.py
├── cycle_exclusion_engine/         (Iterations 072–075, frozen)
│   ├── rust/                       (cee_rust crate)
│   ├── julia/                      (CEEJulia package)
│   ├── scripts/run_cycle_engine.{sh,py}
│   ├── shared/FORMAT.md
│   ├── NOTE_periodic_word_engine.md   ← citable engineering note
│   └── reports/2026-04-28-bench.md
├── proof_states/                   (per-iteration JSON proof-states)
├── certificates/                   (LP certificates, exact rational)
├── witnesses/                      (cycle witness JSON, classified)
├── RESEARCH_AUDIT_2026-04-28.md    ← LP-branch closure document
├── EDITORIAL_REVIEW_2026-04-28.md  ← skeptical editor's pass
├── iteration_077_diophantine_handoff_DESIGN.md  ← next-branch design
├── changelog.md
├── program.md                      ← agent rules / proof protocol
└── RUN_NOTES.md                    ← per-run history (legacy README)
```

---

## Reproduce

### Branch I — exact verification of the $K = 8$ certificate

```bash
cd ~/Downloads/collatz-proof-work
ITER_K=8 python3 experiments/iteration_069_audit.py
# expect: 0 / 12,711,807 failures under exact Fraction(LOG2_3_UPPER) arithmetic
```

### Branch II — periodic-word exclusion through $T \le 36$

```bash
cd cycle_exclusion_engine

# All tests
make test                              # 25 Rust + 20 Julia tests

# Scan T <= 24 (default mode 072: classifier + theorem + analyzer)
python3 scripts/run_cycle_engine.py

# Scan T <= 36 (~5–6 minutes on Apple M-series single-thread)
T_MAX=36 RUN_TAG=T36 \
  ANALYZER_PRECISION_BITS=768 \
  ANALYZER_SHORTLIST_SIZE=100 \
  python3 scripts/run_cycle_engine.py

# Theorem-only mode (Iteration 074)
CEE_PIPELINE_MODE=074 python3 scripts/run_cycle_engine.py
```

Each invocation writes a manifest to `manifests/`, per-stage proof_state
files to `proof_states/`, NDJSON to `out/`, candidate exports to
`candidates/`, and per-stage logs to `logs/`.

### Throughput reference (Apple M-series, single-thread)

| Stage / range                     | Records           | Time   |
|---|---:|---:|
| Rust open-word $K = 36$          | 39,088,169 ($F_{38}$) | 41 s  |
| Rust periodic $T \le 24$         | 12,216            | 0.25 s |
| End-to-end $T \le 24$             | 12,216            | ~7.5 s |
| End-to-end $T \le 36$             | 2,552,323         | 327 s |

---

## Tags

| Tag                                | Commit  | Meaning                                                                         |
|------------------------------------|---------|---------------------------------------------------------------------------------|
| `cee-frozen-2026-04-28`            | preserved | CEE branch frozen at the engineering checkpoint (T ≤ 36 clean, T ≤ 48 deferred). |
| `iteration-077-design-2026-04-28`  | preserved | Diophantine-handoff design ready to consume CEE OPEN_CANDIDATE exports.         |
| `preprint-ready-2026-04-28`        | preserved | Editorial fixes applied; claim discipline GREEN.                                 |

---

## Limitations and non-claims

1. We do **not** prove the Collatz conjecture, nor any partial result
   that is not already supplied by the cited literature
   ([Hercher 2022](https://arxiv.org/abs/2201.00406);
   [Tao 2019](https://arxiv.org/abs/1909.03562);
   [Eliahou 1993](https://doi.org/10.1016/0012-365X%2893%2990052-U);
   [Krasikov–Lagarias 2003](https://doi.org/10.4064/aa109-3-3);
   Lagarias 1985).
2. The Branch I certificate is a statement about a specific finite
   directed graph derived from $n_0 \bmod 2^{3K}$ at $K = 8$. It is
   *not* a statement about Collatz dynamics on positive integers.
   The semantic-gap diagnostic (Iter. 069b, 071B) is part of the
   result, not a footnote.
3. The Branch I $-\lambda \cdot S$ reweighting is a *cycle-level*
   correction. By a per-edge fuel audit and a realised-trajectory
   LP re-solve, it is *not* a per-edge Lyapunov descent term on
   positive integers.
4. The Branch II engine is an **exclusion engine**, not a proof
   engine. It does not re-prove [Hercher 2022](https://arxiv.org/abs/2201.00406)'s
   $m \ge 92$ bound nor the trusted finite-verification bound (Roosendaal-class);
   both are imported by reference, with full provenance in every
   relevant verdict.
5. The Branch II $T \le 48$ row is **disk-limited; deferred**. It is
   not a partial mathematical exclusion; it is an aborted engineering
   attempt.
6. The Branch II analyzer (Iter. 072.6) ranks candidates by
   $\Delta = |\,m \log 3 - S \log 2\,|$. This is a diagnostic ranking,
   not an exclusion mechanism.
7. The Iteration 077 design is a design document; no verdict produced
   from any current artefact in this work depends on 077.
8. We make no claim about non-cyclic divergent orbits.
   [Tao 2019](https://arxiv.org/abs/1909.03562) is the relevant
   landmark for almost-all-orbit statements; we do not extend or
   strengthen it.

---

## Citing this repository

If you reference this work, please cite:

```bibtex
@misc{aurascoper2026collatz,
  author       = {aurascoper},
  title        = {{collatz-proof-work}: closed-graph cycle-negativity at $K = 8$ and primitive periodic-word exclusion through $T \le 36$ for the ordinary Collatz map},
  year         = {2026},
  howpublished = {\url{https://github.com/aurascoper/collatz-proof-work}},
  note         = {Tag: \texttt{preprint-ready-2026-04-28}; not a proof of the Collatz conjecture.},
}
```

---

## Citations and prior work

- **[Hercher, C. (2022)](https://arxiv.org/abs/2201.00406)**. *There are no Collatz-$m$-Cycles with $m \le 91$.* arXiv:2201.00406. Source of the odd-element lower bound used by Branch II's theorem dispatcher.
- **[Tao, T. (2019)](https://arxiv.org/abs/1909.03562)**. *Almost all orbits of the Collatz map attain almost bounded values.* arXiv:1909.03562. Logarithmic-density argument; orthogonal to cycle exclusion but provides landscape context.
- **Eliahou, S. (1993)**. *The 3x+1 problem: new lower bounds on nontrivial cycle lengths.* Discrete Math. **118**, 45–56.
- **Krasikov, I., Lagarias, J. C. (2003)**. *Bounds for the 3x+1 problem using difference inequalities.* Acta Arith. **109**, 237–258.
- **Lagarias, J. C. (1985)**. *The 3x+1 problem and its generalizations.* Amer. Math. Monthly **92**, 3–23.
- **Terras, R. (1976)**. *A stopping time problem on the positive integers.* Acta Arith. **30**, 241–252.
- **[Yolcu, E., Aaronson, S., Heule, M. J. H. (2021)](https://arxiv.org/abs/2105.14697)**. *An Automated Approach to the Collatz Conjecture.* arXiv:2105.14697.
- **[Gonçalves, F., Greenfeld, R., Madrid, J. (2021)](https://arxiv.org/abs/2111.06170)**. *Generalized Collatz Maps with Almost Bounded Orbits.* arXiv:2111.06170.
- **Roosendaal, E.** Ongoing computational verification of Collatz on positive integers up to $\sim 2^{68}$. Used as the trusted finite-verification bound in the Branch II theorem layer.

---

## License

This repository is **dual-licensed**:

- **Code** (Rust crate `cee_rust`, Julia package `CEEJulia`, Python
  experiments under `experiments/`, `verifiers/`, and shell/Python
  runners under `scripts/`): **MIT** — see [`LICENSE-CODE`](LICENSE-CODE).

- **Documentation, research notes, proof-state JSON, and prose
  artefacts** (everything in the project root *.md files,
  `cycle_exclusion_engine/NOTE_periodic_word_engine.md`,
  `RESEARCH_AUDIT_2026-04-28.md`,
  `EDITORIAL_REVIEW_2026-04-28.md`,
  `iteration_077_diophantine_handoff_DESIGN.md`,
  `changelog.md`, `proof_states/*.json`,
  `cycle_exclusion_engine/reports/*.md`): **CC BY 4.0** —
  see [`LICENSE-DOCS`](LICENSE-DOCS).

You may use, modify, and redistribute either category subject to
the terms of the corresponding license, including attribution back
to this repository.

---

## Acknowledgement of scope

> "Green on claim discipline, yellow on mechanical consistency, no
> unresolved red items."

— internal repo summary at `preprint-ready-2026-04-28`.
