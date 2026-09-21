# Two separate models instead of one unified lifecycle-state model

We're building a **lapse model** (for currently-active players) and a
**revival model** (for currently-inactive players) as two independent
binary classifiers, rather than one unified model over lifecycle state
(e.g. a multi-class classifier or a single hazard model spanning both
transitions). The two populations have genuinely different feature windows
(trailing-28-day engagement vs. lifetime history up to lapse) and different
label horizons (28 days vs. 14 days), and a reader coming from the
discrete-time-hazard framing in the source material might expect a single
survival model to cover both directions — this decision forecloses that
without saying so elsewhere, so it's worth recording.

## Considered options

- **One unified model** (e.g. a 3+-state lifecycle classifier, or a single
  hazard model with return as a competing risk): more elegant in theory,
  but the two transitions (active → lapsed, lapsed → returned) don't share
  a natural feature representation — an active player's last-28-days stats
  don't exist for someone who's already gone quiet for months.
- **Two separate models** (chosen): simpler to build, evaluate, and reason
  about independently; matches how the PRD's metrics are already split by
  population. Cost: two models to maintain instead of one, and no shared
  representation learning between "why players leave" and "why players
  come back," which a unified model might otherwise surface.
