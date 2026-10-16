"""Read the simulation map and identify free or blocked cells."""

import json
from dataclasses import dataclass
from pathlib import Path

Cell = tuple[int, int]


@dataclass
class World:
    width: int
    height: int
    start: Cell
    goal: Cell
    obstacles: set[Cell]

    def inside(self, cell: Cell) -> bool:
        """Check whether a cell is inside the map."""
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def free(self, cell: Cell) -> bool:
        """Check whether the robot can enter a cell."""
        return self.inside(cell) and cell not in self.obstacles

    def neighbors(self, cell: Cell):
        """Find free cells immediately beside the current cell."""
        x, y = cell

        nearby_cells = (
            (x + 1, y),
            (x, y + 1),
            (x - 1, y),
            (x, y - 1),
        )

        for next_cell in nearby_cells:
            if self.free(next_cell):
                yield next_cell

    @classmethod
    def load(cls, path: Path):
        """Load and validate a JSON map."""
        data = json.loads(path.read_text(encoding="utf-8"))

        width = data["width"]
        height = data["height"]

        if (
            type(width) is not int
            or type(height) is not int
            or not (2 <= width <= 100 and 2 <= height <= 100)
        ):
            raise ValueError(
                "Map width and height must be integers from 2 to 100."
            )

        def read_cell(value):
            if (
                not isinstance(value, list)
                or len(value) != 2
                or any(type(number) is not int for number in value)
            ):
                raise ValueError(
                    "Each coordinate must be an integer pair: [x, y]."
                )

            return tuple(value)

        world = cls(
            width=width,
            height=height,
            start=read_cell(data["start"]),
            goal=read_cell(data["goal"]),
            obstacles={
                read_cell(item)
                for item in data.get("obstacles", [])
            },
        )

        if not world.free(world.start) or not world.free(world.goal):
            raise ValueError(
                "Start and goal must be inside the map and unblocked."
            )

        if any(not world.inside(cell) for cell in world.obstacles):
            raise ValueError("All obstacles must be inside the map.")

        return world