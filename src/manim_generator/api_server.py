"""CLI entry point for running the FastAPI server."""

import argparse
import uvicorn


def main():
    """Run the FastAPI server."""
    parser = argparse.ArgumentParser(description="Run the Manim Video Generator API server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    args = parser.parse_args()

    uvicorn.run(
        "manim_generator.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

