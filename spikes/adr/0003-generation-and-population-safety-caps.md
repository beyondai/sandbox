# simulate() enforces both a generation cap and a population cap

Some Life patterns never stabilize - a glider gun keeps emitting a new
glider every 30 generations forever - so a naive "loop until told to stop"
runner can grow the alive-cell set (and render output) without bound. The
64-bit int64 coordinate boundary was also considered a risk, but is not
reachable in practice: a glider drifting steadily would need roughly
3.7 x 10^19 generations to reach it, on the order of a thousand years even
at a billion generations/second. Population growth from non-stabilizing
patterns is the actual reachable worst case, so `simulate(alive,
max_generations, bounds=None, max_population=None)` was added: a generator
yielding `(generation, alive_cells)` up to `max_generations`, raising
`SimulationLimitExceeded` the moment alive-cell count exceeds
`max_population` - checked on the initial state too, not just after each
step.

## Considered options

- **Only cap generations**, rely on the caller to notice runaway population:
  rejected - a fast-growing pattern (e.g. a gun) could exhaust memory well
  within the generation cap.
- **Only cap population**, run indefinitely otherwise: rejected - a stable,
  low-population pattern (e.g. a single blinker) would then run forever with
  no natural stopping point.
- **Both caps together** (chosen): the generation cap bounds runtime even for
  low-population patterns that never trip the population cap; the population
  cap bounds memory even for short runs with explosive growth.
- **Clip coordinates at int64 min/max**: still an open question, not decided
  either way - the boundary isn't reachable by any realistic input or
  generation count, so it's a spec-conformance question rather than a
  practical risk. Not addressed by this ADR.
