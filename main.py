"""Start the autonomous navigation simulation."""

import argparse
from pathlib import Path

from src.world import World
from src.navigation import Navigation
from src.export import save_run


ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(
        description="Run the autonomous navigation simulation."
    )

    parser.add_argument(
        "--map",
        type=Path,
        default=ROOT / "maps" / "warehouse.json",
        help="Path to the simulation map.",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in the terminal without opening the browser.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "outputs",
        help="Folder for saved results.",
    )

    args = parser.parse_args()

    try:
        world = World.load(args.map)
        robot = Navigation(world)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(f"Cannot load map: {error}")

    if args.headless:
        robot.plan()

        for _ in range(world.width * world.height):
            if robot.status in ("ARRIVED", "NO_PATH"):
                break

            robot.step()

        report_path, image_path = save_run(
            robot,
            args.output,
        )

        print(f"Status: {robot.status}")
        print(f"Moves: {len(robot.trail) - 1}")
        print(f"Plans: {robot.plans}")
        print(f"Report: {report_path}")
        print(f"Image: {image_path}")

        return 0 if robot.status == "ARRIVED" else 2

    from src.browser_ui import run

    run(robot, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())