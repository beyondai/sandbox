# Render alive cells as per-cluster ASCII blocks, not one global grid

The sample input has alive cells separated by trillions of units (a glider
near the origin, plus pairs of cells near `(-2e12, -2e12)` and
`(3e12, 3e12)`). A single ASCII grid sized to the bounding box of *all* alive
cells would need trillions of rows and columns, which can't be printed or
even allocated as a string. `render()` instead groups alive cells into
connected components via a flood-fill with a configurable gap threshold
(`cluster_cells()`, default gap 2), then renders each component's own small
bounding box independently, labeled with its coordinate range.

## Considered options

- **Single global bounding box** over all alive cells: rejected - clusters in
  the sample input are ~5 trillion cells apart, so the grid would be
  astronomically large.
- **Cap total render size, truncate anything beyond a threshold**: rejected -
  would silently hide alive clusters from the output instead of showing
  everything.
- **Connected-component clustering with one small block per cluster**
  (chosen): render cost is proportional to each cluster's own size, not the
  distance between clusters, so widely separated small patterns stay
  printable regardless of how far apart they are.
