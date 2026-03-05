"""CLI entry point for the API server."""

from __future__ import annotations

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="AC Race Engineer API server")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "57832")),
        help="Port to listen on (default: PORT env var or 57832)",
    )
    args = parser.parse_args()

    import uvicorn

    uvicorn.run("api.main:create_app", factory=True, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
