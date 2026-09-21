implement Conway's Game of Life for a 64-bit integer coordinate space, in the language of your choice.

The world is a 2D grid of cells addressed by integer coordinates (x, y). Each cell is either "alive" or "dead". The simulation advances in discrete generations: at each tick, every cell updates simultaneously according to these rules:

An alive cell with fewer than 2, or more than 3, alive neighbors (among its 8 surrounding cells) becomes dead.
A dead cell with exactly 3 alive neighbors becomes alive.
All other cells keep their current state.

Your input is a list of alive (x, y) coordinates. They can be anywhere in the signed 64-bit integer range, so the board can be very large.

Sample input:

(0, 1)
(1, 2)
(2, 0)
(2, 1)
(2, 2)
(-2000000000000, -2000000000000)
(-2000000000001, -2000000000001)
(3000000000000, 3000000000000)
(3000000000000, 3000000000001)
(3000000000001, 3000000000000)
(3000000000001, 3000000000001)