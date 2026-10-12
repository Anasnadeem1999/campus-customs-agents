"""Regenerate `.mcp.json` for the machine it is run on.

The committed `.mcp.json` holds an absolute path to this project's virtual
environment, because that is what reliably launches on the author's machine.
Absolute paths do not survive a clone, so anyone else -- a grader, or the
author on a different machine -- runs this once and the config is rewritten
for them:

    python scripts/setup_mcp_config.py

It finds the venv interpreter for the current platform (`Scripts/python.exe`
on Windows, `bin/python` elsewhere), falling back to whichever interpreter is
running this script, and writes the same server entry pointing at it.

    python scripts/setup_mcp_config.py --check   # report drift, write nothing
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / ".mcp.json"
SERVER_NAME = "campus-customs"


def venv_python() -> Path:
    """The project venv's interpreter, or the one running this script."""
    candidates = [
        REPO_ROOT / ".venv" / "Scripts" / "python.exe",  # Windows
        REPO_ROOT / ".venv" / "bin" / "python",  # macOS / Linux
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(sys.executable)


def build_config() -> dict:
    return {
        "mcpServers": {
            SERVER_NAME: {
                "command": venv_python().as_posix(),
                "args": ["-m", "mcp_server.server"],
                "env": {
                    # Set so the package imports regardless of the working
                    # directory the host happens to launch the server from.
                    "PYTHONPATH": REPO_ROOT.as_posix(),
                    # Named here as well as defaulted in code, so the config
                    # itself shows which database the agents will touch.
                    "WORKING_DB_PATH": "data/campus_customs_new.db",
                    "SEED_DB_PATH": "data/campus_customs.db",
                },
            }
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args()

    fresh = build_config()
    interpreter = fresh["mcpServers"][SERVER_NAME]["command"]

    if not Path(interpreter).exists():
        print(f"WARNING: interpreter does not exist: {interpreter}", file=sys.stderr)

    if args.check:
        if not CONFIG.exists():
            print(".mcp.json is missing. Run without --check to create it.")
            return 1
        current = json.loads(CONFIG.read_text(encoding="utf-8"))
        if current == fresh:
            print(f".mcp.json matches this machine. Interpreter: {interpreter}")
            return 0
        print(".mcp.json does not match this machine. Run without --check to rewrite it.")
        print(f"  current : {current.get('mcpServers', {}).get(SERVER_NAME, {}).get('command')}")
        print(f"  expected: {interpreter}")
        return 1

    CONFIG.write_text(json.dumps(fresh, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {CONFIG.relative_to(REPO_ROOT)}")
    print(f"  server     : {SERVER_NAME}")
    print(f"  interpreter: {interpreter}")
    print("Restart the vibe coder to pick the server up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
