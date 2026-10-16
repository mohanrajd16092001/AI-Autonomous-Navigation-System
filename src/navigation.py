"""Move the robot along its route and replan after obstacle changes."""

from time import perf_counter

from .planner import astar
from .world import World


class Navigation:
    def __init__(self, world: World):
        self.world = world
        self.reset()

    def reset(self):
        """Return the robot to its starting position."""
        self.position = self.world.start
        self.trail = [self.position]
        self.route = []

        self.status = "READY"
        self.plans = 0
        self.expanded = 0
        self.planning_ms = 0.0
        self.events = []

    def plan(self):
        """Calculate a route from the current position."""
        before = perf_counter()

        result = astar(
            self.world,
            self.position,
            self.world.goal,
        )

        self.planning_ms += (perf_counter() - before) * 1000
        self.expanded += result.expanded
        self.plans += 1
        self.route = result.path

        if self.position == self.world.goal:
            self.status = "ARRIVED"
        elif self.route:
            self.status = "PLANNED"
        else:
            self.status = "NO_PATH"

        self.events.append({
            "type": "plan",
            "position": self.position,
            "path": self.route[:],
            "status": self.status,
        })

    def step(self):
        """Move one cell toward the destination."""
        if self.position == self.world.goal:
            self.status = "ARRIVED"
            return

        if not self.route or any(
            not self.world.free(cell)
            for cell in self.route
        ):
            self.plan()

        if len(self.route) < 2:
            return

        next_cell = self.route[1]

        if next_cell not in set(
            self.world.neighbors(self.position)
        ):
            raise RuntimeError(
                "Controller rejected an invalid movement."
            )

        self.position = next_cell
        self.trail.append(next_cell)
        self.route = self.route[1:]

        if self.position == self.world.goal:
            self.status = "ARRIVED"
        else:
            self.status = "MOVING"

        self.events.append({
            "type": "move",
            "position": self.position,
        })

    def toggle_obstacle(self, cell):
        """Add or remove an obstacle and calculate a new route."""
        protected_cells = (
            self.world.start,
            self.world.goal,
            self.position,
        )

        if (
            not self.world.inside(cell)
            or cell in protected_cells
        ):
            return False

        blocked = cell not in self.world.obstacles

        if blocked:
            self.world.obstacles.add(cell)
        else:
            self.world.obstacles.remove(cell)

        self.events.append({
            "type": "obstacle",
            "position": cell,
            "blocked": blocked,
        })

        self.plan()
        return True

    def report(self):
        """Collect the current run's results."""
        return {
            "status": self.status,
            "start": self.world.start,
            "goal": self.world.goal,
            "position": self.position,
            "moves": len(self.trail) - 1,
            "planning_calls": self.plans,
            "replans": max(0, self.plans - 1),
            "nodes_expanded_total": self.expanded,
            "planning_ms_total": round(self.planning_ms, 3),
            "trajectory": self.trail,
            "remaining_path": self.route,
            "events": self.events,
            "map": {
                "width": self.world.width,
                "height": self.world.height,
                "obstacles": sorted(self.world.obstacles),
            },
            "assumptions": (
                "Known grid; unit costs; four directions; "
                "point robot; no physical sensors."
            ),
        }