"""CLI entry point for sqlite-api."""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="sqlite-api",
        description="Drop a SQLite file, get an instant REST API.",
        epilog='Example: sqlite-api mydb.db --port 3000 --readonly',
    )
    parser.add_argument(
        "database",
        help="Path to the SQLite database file",
    )
    parser.add_argument(
        "--host", "-H",
        default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)",
    )
    parser.add_argument(
        "--readonly", "-r",
        action="store_true",
        help="Read-only mode (no POST/PUT/DELETE)",
    )
    parser.add_argument(
        "--title", "-t",
        default=None,
        help="API title (default: derived from filename)",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="sqlite-api 1.0.0",
    )

    args = parser.parse_args()

    db_path = Path(args.database).expanduser().resolve()

    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    if not db_path.is_file():
        print(f"[ERROR] Not a file: {db_path}", file=sys.stderr)
        sys.exit(1)

    title = args.title or f"SQLite API: {db_path.name}"

    from .server import build_app

    print(f"[*] Loading: {db_path}")
    app = build_app(str(db_path), read_only=args.readonly, title=title)

    import uvicorn

    mode = "read-only" if args.readonly else "read-write"
    print(f"[+] Starting on http://{args.host}:{args.port} ({mode})")
    print(f"    Docs: http://localhost:{args.port}/docs")
    print(f"    API:  http://localhost:{args.port}/api")
    print(f"\n    Press Ctrl+C to stop.\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
