# Sparse alive-cell set, not a dense grid, for the board

The problem states coordinates can be "anywhere in the signed 64-bit integer
range" - the sample input alone has cells around `(-2e12, -2e12)` and
`(3e12, 3e12)`, a bounding box roughly 5 trillion cells wide. A dense 2D
array/grid sized to that would need exabytes of memory, so the board is
represented as a plain `set[Cell]` holding only the alive coordinates.
`step()` computes each generation by counting neighbors of currently-alive
cells with a `Counter`, touching only cells adjacent to something alive -
cost scales with population, not board size.

## Considered options

- **Dense 2D array/grid** sized to the bounding box of alive cells: rejected
  - infeasible for inputs like the sample that span trillions of cells.
- **Dict of `Cell -> bool` for every cell, alive or dead**: rejected as no
  better than a plain set, since only alive state needs to be stored at all;
  dead cells vastly outnumber alive ones everywhere in this problem.
- **`set[Cell]` of alive coordinates only** (chosen): memory and per-generation
  work are both `O(alive cells)`, independent of how far apart cells are or
  how large the coordinate range is.

## Consequences

A pattern that never stabilizes (e.g. a glider gun) can still grow the alive
set without bound over many generations, even though board size is no longer
the limiting factor - see ADR 0003 (generation and population safety caps).
