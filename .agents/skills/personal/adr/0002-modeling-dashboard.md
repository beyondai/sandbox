# Modeling dashboard: narrow scope, read-only from later steps

`ml-modeling-data` now creates an EDA notebook and bootstraps a Streamlit dashboard (`dashboard/app.py`); `ml-modeling-evaluate` writes the dashboard's Final Results section. Two decisions here are worth recording, both raised directly by the user while reviewing the plan.

**Scope: EDA + Final Results only, not a full per-step mirror.** The dashboard's stated purpose is "the go-to easy interface to understand the project and progress... albeit not include all the details" — a summary artifact, not a duplicate of every step's `.md` output. Only EDA and Results pass that bar: distributions/correlations are genuinely easier to read as charts, and final metrics are the payoff. Feature-engineering and single-candidate training rationale are process records already well served by their `.md` files — mirroring them onto the dashboard would just be the same information redundantly displayed. Model comparison (multiagent path) is a free exception: `ml-modeling-multiagent` already writes `train-candidates/<model>/metrics.json` per candidate, unchanged, so the dashboard reads those opportunistically with zero changes to that skill.

**`app.py` is written once and never edited by a later step.** Every contributing step instead writes a small structured JSON file next to its existing `.md` (`01-data.json`, `04-evaluate.json`) — the `.md` stays the authoritative documentation, the `.json` carries just the numbers a chart needs. `app.py` reads whichever of those files exist and renders a section per file found, so the dashboard reflects new progress automatically as the pipeline runs, with no risk of dashboard code drifting from what actually happened.

## Considered Options

Considered having every step (`-features`, `-train`, `-multiagent` included) write its own dashboard section, for a comprehensive live view. Rejected: it would touch three more already-working skill files for information that doesn't actually help someone understand the project's outcome, and directly contradicted the user's own "not include all the details" framing.

Considered having each step patch `app.py` directly instead of writing a separate JSON file the app reads. Rejected: turns every future dashboard change into an N-way coordination problem across skill files, and risks `app.py` drifting out of sync with whichever step last ran.

## Consequences

- Only `ml-modeling-data` and `ml-modeling-evaluate` know about the dashboard at all; `ml-modeling-features`, `ml-modeling-train`, and `ml-modeling-multiagent` remain completely unaware of it and unchanged.
- If a future need arises to show feature or training detail on the dashboard, the right shape is still "step writes JSON, `app.py` reads it" — not editing `app.py` per step. Extending scope later should follow this same pattern, not the rejected alternative.
- The Streamlit background process can die between sessions (e.g. a machine restart); `ml-modeling-evaluate` checks reachability and relaunches if needed, but nothing else in the chain currently does — a step between data and evaluate that wants to guarantee the dashboard is live would need the same check added.
