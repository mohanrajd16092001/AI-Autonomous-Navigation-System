"""Check path planning, movement, obstacle changes, and exports."""

import json
import random
import tempfile
import unittest

from collections import deque
from pathlib import Path

from src.world import World
from src.planner import astar
from src.navigation import Navigation
from src.export import save_run


def bfs_distance(world):
    """Independently calculate the shortest distance for comparison."""
    queue = deque([(world.start, 0)])
    visited = {world.start}

    while queue:
        cell, distance = queue.popleft()

        if cell == world.goal:
            return distance

        for neighbor in world.neighbors(cell):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))

    return None


class NavigationTests(unittest.TestCase):
    def test_shortest_paths(self):
        generator = random.Random(42)

        for map_number in range(60):
            obstacles = {
                (x, y)
                for x in range(9)
                for y in range(8)
                if generator.random() < 0.28
            }

            obstacles -= {(0, 0), (8, 7)}
            world = World(9, 8, (0, 0), (8, 7), obstacles)

            with self.subTest(map_number=map_number):
                result = astar(world, world.start, world.goal)
                expected = bfs_distance(world)

                actual = (
                    len(result.path) - 1
                    if result.path
                    else None
                )

                self.assertEqual(actual, expected)

                for current, following in zip(
                    result.path, result.path[1:]
                ):
                    self.assertIn(
                        following,
                        set(world.neighbors(current)),
                    )

    def test_replanning(self):
        world = World(7, 5, (0, 2), (6, 2), set())
        robot = Navigation(world)

        robot.plan()
        robot.step()

        blocked_cell = robot.route[1]
        robot.toggle_obstacle(blocked_cell)

        for _ in range(40):
            if robot.status == "ARRIVED":
                break
            robot.step()

        self.assertEqual(robot.status, "ARRIVED")
        self.assertNotIn(blocked_cell, robot.trail)
        self.assertGreaterEqual(robot.plans, 2)

    def test_unreachable_goal(self):
        wall = {(1, y) for y in range(4)}
        world = World(4, 4, (0, 0), (3, 3), wall)
        robot = Navigation(world)

        robot.step()

        self.assertEqual(robot.status, "NO_PATH")
        self.assertEqual(robot.position, (0, 0))

    def test_start_equals_goal(self):
        world = World(3, 3, (1, 1), (1, 1), set())
        robot = Navigation(world)

        robot.step()

        self.assertEqual(robot.status, "ARRIVED")
        self.assertEqual(len(robot.trail), 1)

    def test_protected_cells_and_reset(self):
        world = World(5, 5, (0, 0), (4, 4), set())
        robot = Navigation(world)

        self.assertFalse(robot.toggle_obstacle((0, 0)))
        self.assertFalse(robot.toggle_obstacle((4, 4)))
        self.assertFalse(robot.toggle_obstacle((-1, 0)))

        robot.step()

        self.assertFalse(
            robot.toggle_obstacle(robot.position)
        )

        robot.reset()

        self.assertEqual(robot.position, world.start)
        self.assertEqual(robot.plans, 0)

    def test_exports_and_invalid_map(self):
        world = World(3, 3, (0, 0), (2, 2), set())
        robot = Navigation(world)
        robot.plan()

        with tempfile.TemporaryDirectory() as folder:
            report, image = save_run(robot, Path(folder))

            saved_report = json.loads(
                report.read_text(encoding="utf-8")
            )

            self.assertEqual(
                saved_report["status"],
                "PLANNED",
            )

            self.assertIn(
                "<svg",
                image.read_text(encoding="utf-8"),
            )

            invalid_map = Path(folder) / "invalid.json"
            invalid_map.write_text(
                json.dumps({
                    "width": 3,
                    "height": 3,
                    "start": [0, 0],
                    "goal": [2, 2],
                    "obstacles": [[0, 0]],
                }),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                World.load(invalid_map)


if __name__ == "__main__":
    unittest.main()