import argparse
import asyncio
import json
import os
from pathlib import Path

from scripts.base import BaseScript
from src.operations.preflight import PreflightInput, run_preflight
from src.settings import get_settings


class PreflightScript(BaseScript):
    name = "preflight"
    description = "Run generic read-only database and write-cutover safety checks."

    def configure_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--database-url", default="", help="Database URL to inspect. Defaults to Settings.database_url."
        )
        parser.add_argument(
            "--production",
            action="store_true",
            help="Use PRODUCTION_DATABASE_URL_READONLY unless --write-cutover is also set.",
        )
        parser.add_argument(
            "--write-cutover",
            action="store_true",
            help="Validate write-capable cutover gates before inspecting the write database URL.",
        )
        parser.add_argument(
            "--cutover-confirmed",
            action="store_true",
            help="Required with --write-cutover to prove the caller intentionally selected write mode.",
        )
        parser.add_argument("--backup-path", default="", help="Required with --write-cutover.")
        parser.add_argument("--expected-head", action="append", default=[], help="Expected Alembic head revision.")
        parser.add_argument("--table", action="append", default=[], help="Table to count. May be repeated.")
        parser.add_argument("--output", type=Path, default=None, help="Optional JSON report path.")

    def run(self, args: argparse.Namespace) -> int:
        settings = get_settings()
        database_url = _database_url(args, settings)
        preflight = PreflightInput(
            database_url=database_url,
            expected_heads=tuple(args.expected_head),
            tables=tuple(args.table),
            write_cutover=args.write_cutover,
            cutover_confirmed=args.cutover_confirmed,
            backup_path=args.backup_path,
            mode="production" if args.production else settings.APP_ENV,
        )
        report = asyncio.run(run_preflight(preflight))
        output = json.dumps(report, indent=2, default=str) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        print(output, end="")
        return 0 if report["status"] == "pass" else 1


def _database_url(args: argparse.Namespace, settings) -> str:
    if args.database_url:
        return args.database_url
    if args.production and not args.write_cutover:
        return os.environ.get("PRODUCTION_DATABASE_URL_READONLY", "")
    return settings.database_url


if __name__ == "__main__":
    raise SystemExit(PreflightScript().execute())
