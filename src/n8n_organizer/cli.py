from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .main import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="n8n-organizer",
        description="Classify n8n workflow JSON files and write category-level Markdown files.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="scan a folder and write the knowledge base")
    build.add_argument("--input", required=True, type=Path, help="folder with n8n workflow JSON files")
    build.add_argument("--output", required=True, type=Path, help="folder for the Markdown output")
    build.add_argument("--log-dir", type=Path, default=Path("logs"), help="folder for JSONL traces (default: ./logs)")
    build.add_argument("--debug", action="store_true", help="also print trace lines to stderr")

    search = sub.add_parser("search", help="search the built knowledge base (not built yet)")
    search.add_argument("query", help="text to search for")
    return parser


def search(query: str) -> None:
    raise NotImplementedError("search is planned (workflow search index) but not built yet")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            run(input_dir=args.input, output_dir=args.output)
        elif args.command == "search":
            search(args.query)
    except NotImplementedError as exc:
        print(f"n8n-organizer: {exc}", file=sys.stderr)
        return 2
    return 0
