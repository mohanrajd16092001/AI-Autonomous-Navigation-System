"""Save navigation results as a JSON report and an SVG map image."""

import json
from datetime import datetime, timezone
from pathlib import Path


def save_run(nav, directory: Path):
    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S_%fZ"
    )

    report_path = directory / f"run_{timestamp}.json"
    image_path = directory / f"run_{timestamp}.svg"

    report_path.write_text(
        json.dumps(nav.report(), indent=2),
        encoding="utf-8",
    )

    scale = 32
    width = nav.world.width * scale
    height = nav.world.height * scale

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height + 60}" '
            f'viewBox="0 0 {width} {height + 60}">'
        ),
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
    ]

    # Draw free cells and obstacles.
    for y in range(nav.world.height):
        for x in range(nav.world.width):
            if (x, y) in nav.world.obstacles:
                color = "#334155"
            else:
                color = "#ffffff"

            parts.append(
                f'<rect x="{x * scale}" y="{y * scale}" '
                f'width="{scale}" height="{scale}" '
                f'fill="{color}" stroke="#cbd5e1"/>'
            )

    # Draw the travelled path and the remaining route.
    paths = (
        (nav.trail, "#0891b2"),
        (nav.route, "#f59e0b"),
    )

    for path, color in paths:
        if len(path) > 1:
            points = " ".join(
                f"{(x + 0.5) * scale},{(y + 0.5) * scale}"
                for x, y in path
            )

            parts.append(
                f'<polyline points="{points}" fill="none" '
                f'stroke="{color}" stroke-width="5"/>'
            )

    # Mark the start, goal, and robot.
    markers = (
        (nav.world.start, "#16a34a", "S"),
        (nav.world.goal, "#dc2626", "G"),
        (nav.position, "#2563eb", "R"),
    )

    for cell, color, label in markers:
        x = (cell[0] + 0.5) * scale
        y = (cell[1] + 0.5) * scale

        parts.append(
            f'<circle cx="{x}" cy="{y}" r="12" '
            f'fill="{color}"/>'
        )

        parts.append(
            f'<text x="{x}" y="{y + 5}" '
            f'text-anchor="middle" font-family="Arial" '
            f'font-size="14" fill="white">{label}</text>'
        )

    moves = len(nav.trail) - 1

    parts.append(
        f'<text x="10" y="{height + 25}" '
        f'font-family="Arial" font-size="14">'
        f'{nav.status} | moves: {moves} | plans: {nav.plans}'
        f'</text>'
    )

    parts.append(
        f'<text x="10" y="{height + 48}" '
        f'font-family="Arial" font-size="12">'
        f'Blue robot | cyan travelled | amber remaining'
        f'</text>'
    )

    parts.append("</svg>")

    image_path.write_text(
        "\n".join(parts),
        encoding="utf-8",
    )

    return report_path, image_path