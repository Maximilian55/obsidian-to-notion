from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from .config import ConfigurationError, DatabaseRoute, EnvConfig, load_env_file
from .exporter import export_note
from .notion_client import NotionClient
from .parser import parse_note


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a single Obsidian note into Notion.")

    parser.add_argument("--env", default=".env", help="Path to the .env file with Notion credentials.")
    parser.add_argument("--send", action="store_true", help="Actually create pages in Notion.")
    parser.add_argument("--skip-lookups", action="store_true", help="Skip relation lookups for dry runs.")
    parser.add_argument("note_path", help="Markdown file to export.")
    return parser


def route_for_note(note_path: Path, env: EnvConfig) -> DatabaseRoute:
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
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    env_config = load_env_file(Path(args.env))
    client = NotionClient(env_config.token) if (args.send or not args.skip_lookups) else None

    note_path = Path(args.note_path)
    note = parse_note(note_path)
    database = route_for_note(note_path, env_config)
    result = export_note(
        note
        ,env_config
        ,database
        ,client=client
        ,skip_lookups=args.skip_lookups
        ,send_to_notion=args.send
    )

    print(f"[info] Processed {note.path}")

    if result.missing_organizations:
        print(f"[warn] Missing organizations: {', '.join(result.missing_organizations)}")
    if result.missing_projects:
        print(f"[warn] Missing projects: {', '.join(result.missing_projects)}")
    if result.missing_participants:
        print(f"[warn] Missing participants {', '.join(result.missing_participants)}")

    if not args.send:
        print(json.dumps(result.payload, indent=2))
    else:
        print(f"[info] Created Notion page: {result.notion_url}")
