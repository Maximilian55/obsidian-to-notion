from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Optional

from .config import ConfigurationError, DatabaseRoute, EnvConfig, load_env_file
from .exporter import export_note
from .notion_client import NotionClient
from .parser import parse_note


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser for the exporter CLI."""

    parser = argparse.ArgumentParser(description="Export a single Obsidian note into Notion.")
    parser.add_argument("--env", default=".env", help="Path to the .env file with Notion credentials.")
    parser.add_argument("--send", action="store_true", help="Actually create pages in Notion.")
    parser.add_argument("--skip-lookups", action="store_true", help="Skip relation lookups for dry runs.")
    parser.add_argument(
        "--debug-log",
        action="store_true",
        help="Write full payloads and Notion responses to export.debug.log",
    )
    parser.add_argument("note_path", help="Markdown file to export.")
    return parser


def route_for_note(note_path: Path, env: EnvConfig) -> DatabaseRoute:
    """Determine which Notion database a note should target based on its filesystem path."""

    resolved_path = note_path.resolve()

    def path_matches(base: Optional[Path]) -> bool:
        if not base:
            return False
        try:
            resolved_path.relative_to(base.resolve())
            return True
        except ValueError:
            return False

    target_db: Optional[str] = None
    if path_matches(env.meetings_vault_path) and env.default_meetings_db_id:
        target_db = env.default_meetings_db_id
    elif path_matches(env.notes_vault_path) and env.default_notes_db_id:
        target_db = env.default_notes_db_id
    else:
        raise ConfigurationError(
            "No target Notion database configured. Please set MEETINGS_DB_ID or NOTES_DB_ID in .env."
        )

    return DatabaseRoute(
        target_db_id=target_db
        ,organizations_db_id=env.default_organizations_db_id
        ,projects_db_id=env.default_projects_db_id
        ,participants_db_id=env.default_participants_db_id
    )


def run_cli(argv: Optional[list[str]] = None) -> None:
    """Entry point invoked by export_note_to_notion.py or tests."""

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logger = configure_logging()
    debug_logger = configure_debug_logger() if args.debug_log else None

    env_config = load_env_file(Path(args.env))
    client = NotionClient(env_config.token) if (args.send or not args.skip_lookups) else None

    note_path = Path(args.note_path)
    logger.info("Starting export for %s", note_path)
    note = parse_note(note_path)
    database = route_for_note(note_path, env_config)
    result = export_note(
        note
        ,env_config
        ,database
        ,client=client
        ,skip_lookups=args.skip_lookups
        ,send_to_notion=args.send
        ,debug_logger=debug_logger
    )

    print(f"[info] Processed {note.path}")
    logger.info("Processed %s", note.path)

    if result.missing_organizations:
        missing_orgs = ", ".join(result.missing_organizations)
        print(f"[warn] Missing organizations: {missing_orgs}")
        logger.warning("Missing organizations for %s: %s", note.path, missing_orgs)
    if result.missing_projects:
        missing_projects = ", ".join(result.missing_projects)
        print(f"[warn] Missing projects: {missing_projects}")
        logger.warning("Missing projects for %s: %s", note.path, missing_projects)
    if result.missing_participants:
        missing_participants = ", ".join(result.missing_participants)
        print(f"[warn] Missing participants {missing_participants}")
        logger.warning("Missing participants for %s: %s", note.path, missing_participants)
        for participant in result.missing_participants:
            print(f"⚠ Missing participant for Notion lookup: {participant}")
    if result.missing_organizations:
        for org in result.missing_organizations:
            print(f"⚠ Missing organization for Notion lookup: {org}")
    if result.missing_projects:
        for proj in result.missing_projects:
            print(f"⚠ Missing project for Notion lookup: {proj}")

    if not args.send:
        print(json.dumps(result.payload, indent=2))
        logger.info("Dry-run complete for %s", note.path)
        if debug_logger:
            debug_logger.info("Payload for %s:\n%s", note.path, json.dumps(result.payload, indent=2))
    else:
        print(f"[info] Created Notion page: {result.notion_url}")
        logger.info("Created Notion page for %s at %s", note.path, result.notion_url)
LOG_PATH = Path(__file__).resolve().parent.parent / "export.log"
DEBUG_LOG_PATH = Path(__file__).resolve().parent.parent / "export.debug.log"
LOGGER_NAME = "obsidian_to_notion"


def configure_logging() -> logging.Logger:
    """Set up the primary info-level logger that writes to export.log."""

    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    return logger


def configure_debug_logger() -> logging.Logger:
    """Create or return the debug logger that captures payloads/API responses."""
    
    debug_logger = logging.getLogger(f"{LOGGER_NAME}.debug")
    if not debug_logger.handlers:
        debug_logger.setLevel(logging.INFO)
        handler = logging.FileHandler(DEBUG_LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [DEBUG] %(message)s"))
        debug_logger.addHandler(handler)
    return debug_logger
