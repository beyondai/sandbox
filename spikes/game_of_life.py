"""Conway's Game of Life over a sparse, unbounded (64-bit) integer coordinate space.

The board isn't stored as a dense grid (it could be up to 2^64 cells wide) -
just a set of the coordinates that are alive. Each generation, we only need to
look at alive cells and their neighbors to know what changes.
"""

from collections import Counter
from collections.abc import Iterator

Cell = tuple[int, int]


class SimulationLimitExceeded(Exception):
    """Raised when a run exceeds a configured safety limit (generations or
    alive-cell population). Guards against patterns that never stabilize -
    e.g. a glider gun keeps emitting new gliders forever, so alive-cell count
    (and per-generation work) grows without bound if nothing stops it.
    """

NEIGHBOR_OFFSETS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]


def step(alive: set[Cell], bounds: tuple[Cell, Cell] | None = None) -> set[Cell]:
    """Advance one generation. If `bounds` is given as ((min_x, min_y), (max_x,
    max_y)), cells outside that box are clipped (die off) - used to test on a
    smaller board before trusting the unbounded 64-bit version.
    """
    neighbor_counts: Counter[Cell] = Counter()
    for x, y in alive:
        for dx, dy in NEIGHBOR_OFFSETS:
            neighbor_counts[(x + dx, y + dy)] += 1

    next_alive = set()
    for cell, count in neighbor_counts.items():
        if count == 3 or (count == 2 and cell in alive):
            next_alive.add(cell)

    if bounds is not None:
        (min_x, min_y), (max_x, max_y) = bounds
        next_alive = {(x, y) for x, y in next_alive if min_x <= x <= max_x and min_y <= y <= max_y}

    return next_alive


def simulate(
    alive: set[Cell],
    max_generations: int,
    bounds: tuple[Cell, Cell] | None = None,
    max_population: int | None = None,
) -> Iterator[tuple[int, set[Cell]]]:
    """Yield (generation, alive_cells) starting at generation 0, advancing one
    step at a time up to `max_generations` (the generation-count safety cap).

    If `max_population` is given, raises SimulationLimitExceeded as soon as
    the alive-cell count exceeds it - checked on the initial state too, not
    just after each step.
    """

    def check_population(generation: int, cells: set[Cell]) -> None:
        if max_population is not None and len(cells) > max_population:
            raise SimulationLimitExceeded(
                f"generation {generation}: {len(cells)} alive cells exceeds max_population={max_population}"
            )

    check_population(0, alive)
    yield 0, alive
    for generation in range(1, max_generations + 1):
        alive = step(alive, bounds)
        check_population(generation, alive)
        yield generation, alive


def cluster_cells(alive: set[Cell], gap: int = 2) -> list[set[Cell]]:
    """Group alive cells into connected clusters, so far-apart cells (e.g.
    coordinates trillions apart) don't force one giant render.
    """
    remaining = set(alive)
    clusters = []
    while remaining:
        seed = next(iter(remaining))
        cluster = {seed}
        frontier = [seed]
        remaining.discard(seed)
        while frontier:
            x, y = frontier.pop()
            for nx in range(x - gap, x + gap + 1):
                for ny in range(y - gap, y + gap + 1):
                    if (nx, ny) in remaining:
                        remaining.discard((nx, ny))
                        cluster.add((nx, ny))
                        frontier.append((nx, ny))
        clusters.append(cluster)
    return clusters


def render_cluster(cluster: set[Cell]) -> str:
    xs = [x for x, _ in cluster]
    ys = [y for _, y in cluster]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    lines = [f"({min_x}, {min_y}) - ({max_x}, {max_y})"]
    for y in range(min_y, max_y + 1):
        row = "".join("#" if (x, y) in cluster else "." for x in range(min_x, max_x + 1))
        lines.append(row)
    return "\n".join(lines)


def render(alive: set[Cell]) -> str:
    if not alive:
        return "(empty)"
    return "\n\n".join(render_cluster(c) for c in cluster_cells(alive))


SAMPLE_INPUT: list[Cell] = [
    (0, 1),
    (1, 2),
    (2, 0),
    (2, 1),
    (2, 2),
    (-2000000000000, -2000000000000),
    (-2000000000001, -2000000000001),
    (3000000000000, 3000000000000),
    (3000000000000, 3000000000001),
    (3000000000001, 3000000000000),
    (3000000000001, 3000000000001),
]


BOARD_SIZE = 1024
BOARD_BOUNDS: tuple[Cell, Cell] = ((0, 0), (BOARD_SIZE - 1, BOARD_SIZE - 1))

# The glider from SAMPLE_INPUT, shifted to sit well inside a 1024x1024 board.
GLIDER_OFFSET: Cell = (500, 500)
GLIDER_TEST_INPUT: list[Cell] = [
    (0 + GLIDER_OFFSET[0], 1 + GLIDER_OFFSET[1]),
    (1 + GLIDER_OFFSET[0], 2 + GLIDER_OFFSET[1]),
    (2 + GLIDER_OFFSET[0], 0 + GLIDER_OFFSET[1]),
    (2 + GLIDER_OFFSET[0], 1 + GLIDER_OFFSET[1]),
    (2 + GLIDER_OFFSET[0], 2 + GLIDER_OFFSET[1]),
]


# Safety caps for the demo runs below - a real run might pick very different
# values, but *some* cap should always be set so a never-stabilizing pattern
# (e.g. a glider gun) can't grow memory/render output unboundedly.
MAX_GENERATIONS = 4
MAX_POPULATION = 10_000


def run_bounded_test() -> None:
    """Sanity check on a small 1024x1024 board before trusting the full
    64-bit-range run: a known glider should just glide, unaffected by bounds
    since it never nears the edges.
    """
    try:
        for gen, alive in simulate(
            set(GLIDER_TEST_INPUT), MAX_GENERATIONS, bounds=BOARD_BOUNDS, max_population=MAX_POPULATION
        ):
            print(f"=== Bounded test, generation {gen} ({len(alive)} alive) ===")
            print(render(alive))
            print()
    except SimulationLimitExceeded as exc:
        print(f"Stopped early: {exc}")


def run_sample() -> None:
    try:
        for gen, alive in simulate(set(SAMPLE_INPUT), MAX_GENERATIONS, max_population=MAX_POPULATION):
            print(f"=== Generation {gen} ({len(alive)} alive) ===")
            print(render(alive))
            print()
    except SimulationLimitExceeded as exc:
        print(f"Stopped early: {exc}")


def main() -> None:
    run_bounded_test()
    run_sample()


if __name__ == "__main__":
    main()
