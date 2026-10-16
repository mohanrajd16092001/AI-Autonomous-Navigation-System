"""Connect the browser interface to the Python simulation."""

import json
import secrets
import webbrowser

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .export import save_run


def create_server(nav, output_dir, port=0):
    token = secrets.token_urlsafe(32)
    original_obstacles = nav.world.obstacles.copy()

    interface_path = Path(__file__).with_name("interface.html")
    page = interface_path.read_text(encoding="utf-8")
    page = page.replace("__TOKEN__", token)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            """Keep routine browser requests out of the terminal."""
            pass

        def reply(self, code, body, content_type="application/json"):
            raw = body.encode("utf-8")

            self.send_response(code)
            self.send_header(
                "Content-Type",
                content_type + "; charset=utf-8",
            )
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            """Send the simulation screen to the browser."""
            if self.path != "/":
                self.reply(
                    404,
                    json.dumps({"error": "Unknown page"}),
                )
                return

            self.reply(200, page, "text/html")

        def do_POST(self):
            """Handle button presses and obstacle edits."""
            if (
                self.path != "/action"
                or self.headers.get("X-Session") != token
            ):
                self.reply(
                    403,
                    json.dumps({"error": "Invalid session"}),
                )
                return

            try:
                size = int(self.headers.get("Content-Length", 0))

                if not 0 < size <= 1024:
                    raise ValueError("Invalid request size.")

                request = json.loads(self.rfile.read(size))

                if not isinstance(request, dict):
                    raise ValueError("Invalid request.")

                kind = request["kind"]
                files = None

                if kind == "plan":
                    nav.plan()

                elif kind == "step":
                    nav.step()

                elif kind == "reset":
                    nav.world.obstacles = original_obstacles.copy()
                    nav.reset()

                elif kind == "obstacle":
                    cell = request["cell"]

                    if (
                        not isinstance(cell, list)
                        or len(cell) != 2
                        or any(type(value) is not int for value in cell)
                    ):
                        raise ValueError("Invalid cell coordinates.")

                    nav.toggle_obstacle(tuple(cell))

                elif kind == "save":
                    files = [
                        str(path.resolve())
                        for path in save_run(nav, output_dir)
                    ]

                elif kind != "state":
                    raise ValueError("Unknown action.")

                report = nav.report()

                if files:
                    report["files"] = files

                self.reply(200, json.dumps(report))

            except (ValueError, TypeError, KeyError) as error:
                self.reply(
                    400,
                    json.dumps({"error": str(error)}),
                )

            except OSError as error:
                self.reply(
                    500,
                    json.dumps({
                        "error": f"Could not save results: {error}"
                    }),
                )

    return HTTPServer(("127.0.0.1", port), Handler)


def run(nav, output_dir):
    server = create_server(nav, output_dir)
    address = f"http://127.0.0.1:{server.server_port}/"

    print(f"Open simulation: {address}")
    print("Keep this terminal open.")
    print("Press Ctrl+C here to stop the simulation.")

    webbrowser.open(address)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
    finally:
        server.server_close()