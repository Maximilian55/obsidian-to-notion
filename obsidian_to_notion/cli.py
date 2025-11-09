from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from .config import ConfigurationError, DatabaseRoute, EnvConfig, VaultConfig, load_env_file, load_vault_config
from .exporter import export_note
from .notion_client import NotionClient
from .parser import parse_note


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a single Obsidian note into Notion.")

    parser.add_argument("--env", default=".env", help="Path to the .env file with Notion credentials.")
    parser.add_argument("--vault-config", help="Optional JSON config describing vault routing.")
    parser.add_argument("--send", action="store_true", help="Actually create pages in Notion.")
    parser.add_argument("--skip-lookups", action="store_true", help="Skip relation lookups for dry runs.")
    parser.add_argument("note_path", help="Markdown file to export.")
    return parser


def load_configs(env_path: Path, vault_config_path: Optional[Path]) -> tuple[EnvConfig, Optional[VaultConfig]]:
    env_config = load_env_file(env_path)
    vault_config = load_vault_config(vault_config_path) if vault_config_path else None
    return env_config, vault_config


def route_for_note(note_path: Path, vault_config: Optional[VaultConfig], env: EnvConfig) -> DatabaseRoute:
    if vault_config:
        route = vault_config.match_route(note_path)
        if not route:
            raise ConfigurationError(f"No route configured for note {note_path}")
        return route.database

    return DatabaseRoute(
        main_db_id=env.default_main_db_id,
        location_db_id=env.default_location_db_id,
        person_db_id=env.default_person_db_id,
    )


def run_cli(argv: Optional[list[str]] = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    env_config, vault_config = load_configs(Path(args.env), Path(args.vault_config) if args.vault_config else None)
    client = NotionClient(env_config.token) if (args.send or not args.skip_lookups) else None

    note_path = Path(args.note_path)
    note = parse_note(note_path)
    database = route_for_note(note_path, vault_config, env_config)
    result = export_note(
        note,
        env_config,
        database,
        client=client,
        skip_lookups=args.skip_lookups,
        send_to_notion=args.send,
    )

    print(f"[info] Processed {note.path}")
    if result.missing_locations:
        print(f"[warn] Missing locations: {', '.join(result.missing_locations)}")
    if result.missing_people:
        print(f"[warn] Missing people: {', '.join(result.missing_people)}")
    if not args.send:
        print(json.dumps(result.payload, indent=2))
    else:
        print(f"[info] Created Notion page: {result.notion_url}")
