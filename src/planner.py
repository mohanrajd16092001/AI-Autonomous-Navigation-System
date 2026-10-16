"""Find a shortest route using the A* search algorithm."""

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count

from .world import Cell, World


@dataclass
class Plan:
    path: list[Cell]
    expanded: int


def astar(world: World, start: Cell, goal: Cell) -> Plan:
    """Find a route between two free cells."""

    if not world.free(start) or not world.free(goal):
        return Plan([], 0)

    def heuristic(cell):
        """Estimate remaining distance to the goal."""
        return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])

    # Each queue entry contains:
    # estimated total cost, tie breaker, travelled cost, cell.
    serial = count()
    frontier = [(heuristic(start), next(serial), 0, start)]

    costs = {start: 0}
    parents = {}
    expanded = 0

    while frontier:
        _, _, cost, current = heappop(frontier)

        # Skip an older entry if a cheaper route was found.
        if cost != costs.get(current):
            continue

        expanded += 1

        if current == goal:
            path = [current]

            while current in parents:
                current = parents[current]
                path.append(current)

            return Plan(path[::-1], expanded)

        for neighbor in world.neighbors(current):
            next_cost = cost + 1

            if next_cost < costs.get(neighbor, float("inf")):
                costs[neighbor] = next_cost
                parents[neighbor] = current

                heappush(
                    frontier,
                    (
                        next_cost + heuristic(neighbor),
                        next(serial),
                        next_cost,
                        neighbor,
                    ),
                )

    # An empty path means the destination cannot be reached.
    return Plan([], expanded)