"""Correctness tests for the Game of Life rules, run on a small 64x64 board.

Uses the standard library's unittest (no extra dependency needed for a spike).
Run with: python3 -m unittest test_game_of_life.py -v
"""

import unittest

from game_of_life import Cell, SimulationLimitExceeded, simulate, step

BOARD_SIZE = 64
BOUNDS: tuple[Cell, Cell] = ((0, 0), (BOARD_SIZE - 1, BOARD_SIZE - 1))
CENTER = (BOARD_SIZE // 2, BOARD_SIZE // 2)


def shift(cells: set[Cell], offset: Cell = CENTER) -> set[Cell]:
    ox, oy = offset
    return {(x + ox, y + oy) for x, y in cells}


class TestBasicRules(unittest.TestCase):
    def test_underpopulation_lone_cell_dies(self) -> None:
        alive = shift({(0, 0)})
        self.assertEqual(step(alive, BOUNDS), set())

    def test_underpopulation_one_neighbor_dies(self) -> None:
        alive = shift({(0, 0), (1, 0)})
        self.assertEqual(step(alive, BOUNDS), set())

    def test_survival_with_two_neighbors(self) -> None:
        # An L-tromino: (0,0) has neighbors (1,0) and (0,1) -> survives.
        alive = shift({(0, 0), (1, 0), (0, 1)})
        result = step(alive, BOUNDS)
        self.assertIn(shift({(0, 0)}).pop(), result)

    def test_overpopulation_dies(self) -> None:
        # Center cell surrounded by all 8 neighbors dies from overcrowding.
        ring = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
        alive = shift(set(ring) | {(0, 0)})
        result = step(alive, BOUNDS)
        self.assertNotIn(shift({(0, 0)}).pop(), result)

    def test_reproduction_dead_cell_with_three_neighbors_born(self) -> None:
        alive = shift({(0, 0), (1, 0), (0, 1)})
        result = step(alive, BOUNDS)
        self.assertIn(shift({(1, 1)}).pop(), result)


class TestStillLifes(unittest.TestCase):
    """Still lifes should be unchanged by a step."""

    def test_block(self) -> None:
        block = shift({(0, 0), (1, 0), (0, 1), (1, 1)})
        self.assertEqual(step(block, BOUNDS), block)

    def test_beehive(self) -> None:
        beehive = shift({(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (2, 2)})
        self.assertEqual(step(beehive, BOUNDS), beehive)


class TestOscillators(unittest.TestCase):
    """Oscillators should return to their original state after their period."""

    def test_blinker_period_2(self) -> None:
        horizontal = shift({(0, 0), (1, 0), (2, 0)})
        vertical = shift({(1, -1), (1, 0), (1, 1)})

        gen1 = step(horizontal, BOUNDS)
        self.assertEqual(gen1, vertical)

        gen2 = step(gen1, BOUNDS)
        self.assertEqual(gen2, horizontal)

    def test_toad_period_2(self) -> None:
        toad = shift({(1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)})

        gen1 = step(toad, BOUNDS)
        self.assertNotEqual(gen1, toad)

        gen2 = step(gen1, BOUNDS)
        self.assertEqual(gen2, toad)


class TestSpaceships(unittest.TestCase):
    def test_glider_returns_to_same_shape_shifted_after_4_generations(self) -> None:
        glider = shift({(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)})

        alive = glider
        for _ in range(4):
            alive = step(alive, BOUNDS)

        # After 4 generations a glider reproduces its shape, translated by (1, 1).
        expected = shift({(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)}, offset=(CENTER[0] + 1, CENTER[1] + 1))
        self.assertEqual(alive, expected)


class TestBoundedBoard(unittest.TestCase):
    def test_cells_outside_bounds_are_clipped(self) -> None:
        # A blinker positioned so its next state's tips fall outside a tiny board.
        tiny_bounds: tuple[Cell, Cell] = ((0, 0), (2, 2))
        horizontal = {(0, 1), (1, 1), (2, 1)}
        result = step(horizontal, tiny_bounds)
        # Unbounded, this would become the vertical blinker {(1,0),(1,1),(1,2)},
        # which fits in tiny_bounds, so nothing should be clipped here.
        self.assertEqual(result, {(1, 0), (1, 1), (1, 2)})

        # Now push it right up against the edge so part of the next state is cut off.
        edge_bounds: tuple[Cell, Cell] = ((0, 0), (1, 2))
        result = step(horizontal, edge_bounds)
        self.assertEqual(result, {(1, 0), (1, 1), (1, 2)})
        self.assertTrue(all(x <= 1 for x, _ in result))


class TestSimulationLimits(unittest.TestCase):
    def test_simulate_stops_at_max_generations(self) -> None:
        block = shift({(0, 0), (1, 0), (0, 1), (1, 1)})
        results = list(simulate(block, max_generations=5, bounds=BOUNDS))
        self.assertEqual([gen for gen, _ in results], [0, 1, 2, 3, 4, 5])

    def test_simulate_raises_when_initial_population_exceeds_max(self) -> None:
        block = shift({(0, 0), (1, 0), (0, 1), (1, 1)})
        with self.assertRaises(SimulationLimitExceeded):
            list(simulate(block, max_generations=5, bounds=BOUNDS, max_population=3))

    def test_simulate_raises_partway_through_when_population_grows(self) -> None:
        # A glider's population stays at 5 every generation, so a cap of 5
        # should let it run, but a cap of 4 should trip once growth exceeds it.
        glider = shift({(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)})
        list(simulate(glider, max_generations=4, bounds=BOUNDS, max_population=5))  # does not raise

        with self.assertRaises(SimulationLimitExceeded):
            list(simulate(glider, max_generations=4, bounds=BOUNDS, max_population=4))


if __name__ == "__main__":
    unittest.main()
