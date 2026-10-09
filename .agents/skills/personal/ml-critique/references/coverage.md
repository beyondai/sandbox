# Critique coverage map

Contents: How to use | System design skills | Modeling skills | Other
skills

## How to use

Each row is one checklist item or step of a design or modeling skill, with
the catalog IDs that critique it. `sys` = the system catalog
(`../../ml-critique-system/references/catalog.md`), `mod` = the modeling
catalog (`../../ml-critique-modeling/references/catalog.md`).

Keep it current. Reason: a new skill item with no row has no critique
check, and nobody sees the gap.
- When a design or modeling skill adds a checklist item or a step, add a
  row here and a catalog item if no ID covers it.
- When a catalog ID changes, update its rows.

## System design skills

`ml-system-design-definition` (also run by `ml-system-design-prd`):

| Item | Catalog IDs |
|---|---|
| Problem: pain, why now, goal link | sys A1, A2, A3, A7 |
| Problem: ML is necessary, the decision | sys A4, A5, A6 |
| Requirements: scope, out-of-scope | sys C1 |
| Requirements: non-functional | sys C2, C3, C5, C5a |
| Requirements: privacy, compliance | sys C6 |
| Baseline: status quo, floor, build | sys G0 |
| Baseline: recommended baseline | sys G1; mod A2, A3 |
| Metrics: offline | sys B1, B2, B5; mod I1, I2 |
| Metrics: online and guardrails | sys B3, B4, B6 |
| Metrics: intended behavior, ways to game | sys B7; mod I12 |
| Team: stakeholders, dependencies, reuse | sys C7 |

`ml-system-design-high-level`:

| Item | Catalog IDs |
|---|---|
| Framing: task, target, label, horizon | sys D1-D5; mod A1, B2 |
| Framing: population and cadence | sys D6, C4; mod B1 |
| Framing: unit of prediction | sys D8 |
| Framing: exclusions, contamination | sys D7 |
| Framing: intervention, feedback loop | sys D9, D10 |
| Architecture: 2 diagrams, real sources | sys F1, F2, K2 |
| Phasing: V0 baseline, gain per phase | sys H1, H2, H3, G2a |
| Phasing: timeline, headcount | sys H4, K3 |

`ml-system-design-deep-dive`:

| Item | Catalog IDs |
|---|---|
| Data: sources, data engineering | sys E1, E4, E5 |
| Data: cold start | sys E6 |
| Features: list and transforms | sys G1a; mod E1, E2 |
| Features: online/offline parity | sys E2, E3; mod E3, K3 |
| Models: candidates, gate, architecture | sys G2, G2a, G3; mod F1-F4 |
| Training: loss, labels, sampling | sys G4, G5; mod G1, G5, B6, B6a |
| Training: setup and hardware | sys G5a; mod G5a |
| Training: retrain time vs change cadence | sys F7 |
| Serving: mode, stages, budget | sys C4, F3, F4; mod K5 |
| Serving: capacity and cost at peak | sys F4a, C5; mod K4, K5 |

`ml-system-design-delivery`:

| Item | Catalog IDs |
|---|---|
| Fallback: trigger, target, kill switch | sys I6 |
| Execution: milestones, team process | sys I11, H4 |
| Deployment: rollout ramp | sys I5 |
| Deployment: test plan, load test, CI/CD | sys I10, F4a |
| Eval: A/B design and significance | sys I1, I2, I3, I4 |
| Eval: offline method | sys G6; mod C1 |
| Monitoring: health, drift, alerts | sys I7, I8 |
| Retraining, versioning, runbook | sys F5, F6, F7, I9 |

`ml-system-design-post-delivery`:

| Item | Catalog IDs |
|---|---|
| Analysis: why, by segment | sys J1 |
| Explainability | sys J2; mod J1, J2 |
| Iteration: roadmap from launch data | sys J5 |
| Democratize: reusable components | sys J6 |
| Fairness, abuse | sys J3, J4 |

Across sections: sys K1, K2, K3.

## Modeling skills

| Skill: item | Catalog IDs |
|---|---|
| `ml-modeling`: spec and upstream docs | mod A1, I2 |
| `ml-modeling`: proxy data | mod B9 |
| `ml-modeling-data`: labeled table | mod B1, B2, B3, B4, B6a |
| `ml-modeling-data`: profile | mod B5, B8 |
| `ml-modeling-data`: clean | mod B7, B8 |
| Split and CV (data, train) | mod C1, C2, C3 |
| Leakage (data, features) | mod D1-D5 |
| `ml-modeling-features`: transforms | mod E1, E2, E4, E5 |
| `ml-modeling-features`: encodings | mod D3, E4 |
| `ml-modeling-features`: selection | mod E6 |
| `ml-modeling-train`: algorithm | mod F1, F2, F2a |
| `ml-modeling-train`: ranking tasks | mod C2, G1, I11 |
| `ml-modeling-train`: setup, seeds | mod G2-G6 |
| `ml-modeling-train`: tuning | mod H1-H4 |
| `ml-modeling-train`: log each run | mod K2 |
| `ml-modeling-multiagent`: fair compare | mod F3, H2 |
| `ml-modeling-evaluate`: metrics | mod I1, I3, I4, I11 |
| `ml-modeling-evaluate`: baseline | mod A2, A3 |
| `ml-modeling-evaluate`: noise, overfit | mod I5, I6, I8 |
| `ml-modeling-evaluate`: slices, errors | mod I7, I9, I10 |
| `ml-modeling-evaluate`: output review | mod I12; sys B7 |
| `ml-modeling-evaluate`: A/B test | sys I1, I2 |
| `ml-modeling-serve`: mode, serve.py | mod K5, K3 |
| `ml-modeling-serve`: measure, capacity | mod K4, K5 |
| Reproducibility (all steps) | mod K1, K2 |

## Other skills

| Skill: item | Catalog IDs |
|---|---|
| `ml-modeling-autoresearch`: keep a win | mod I6, F4 |
| `ml-system-design-monkey-mode`: baseline | sys G1; mod A2 |
| `ml-system-design-monkey-mlp`: baseline | sys G1; mod A2, F2a |
| Shared: `ml-design-principles.md` | sys G2a, B7; mod F4, I12 |
| Shared: `ml-model-training.md` | sys G5, G5a; mod G5a |
| Shared: `ml-serving.md` | sys F4, F4a; mod K4, K5 |
| Shared: `ml-playbooks.md` | classic mistakes, all lenses |
