from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or malformed."""


@dataclass
class EnvConfig:
    token: str
    default_main_db_id: str
    default_location_db_id: Optional[str] = None
    default_person_db_id: Optional[str] = None


@dataclass
class PropertyMapping:
    name: str = "Name"
    date: Optional[str] = "Date"
    location: Optional[str] = "Location"
    person: Optional[str] = "Person"


@dataclass
class DatabaseRoute:
    main_db_id: str
    location_db_id: Optional[str] = None
    person_db_id: Optional[str] = None
    properties: PropertyMapping = field(default_factory=PropertyMapping)


@dataclass
class VaultRoute:
    folder: str  # path relative to vault root
    database: DatabaseRoute


@dataclass
class VaultConfig:
    vault_path: Path
    routes: List[VaultRoute]

    def match_route(self, file_path: Path) -> Optional[VaultRoute]:
        try:
            relative = file_path.relative_to(self.vault_path)
        except ValueError:
            return None
        for route in self.routes:
            route_folder = Path(route.folder)
            try:
                relative.relative_to(route_folder)
                return route
            except ValueError:
                continue
        return None


def load_env_file(path: Path) -> EnvConfig:
    raw: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        raw[key.strip()] = value.strip().strip('"').strip("'")

    try:
        return EnvConfig(
            token=raw["NOTION_TOKEN"],
            default_main_db_id=raw["MAIN_DB_ID"],
            default_location_db_id=raw.get("LOCATION_ID"),
            default_person_db_id=raw.get("PERSON_ID"),
        )
    except KeyError as missing:
        raise ConfigurationError(f"Missing env var: {missing.args[0]}") from missing


def load_vault_config(path: Path) -> VaultConfig:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Invalid JSON in {path}: {exc}") from exc

    try:
        vault_path = Path(data["vault_path"]).expanduser()
        routes_data = data["routes"]
    except KeyError as missing:
        raise ConfigurationError(f"Missing key in vault config: {missing.args[0]}") from missing

    routes: List[VaultRoute] = []
    for route in routes_data:
        db_raw = route["database"]
        props_raw = db_raw.get("properties", {})
        route_obj = VaultRoute(
            folder=route["folder"],
            database=DatabaseRoute(
                main_db_id=db_raw["main_db_id"],
                location_db_id=db_raw.get("location_db_id"),
                person_db_id=db_raw.get("person_db_id"),
                properties=PropertyMapping(
                    name=props_raw.get("name", "Name"),
                    date=props_raw.get("date", "Date"),
                    location=props_raw.get("location", "Location"),
                    person=props_raw.get("person", "Person"),
                ),
            ),
        )
        routes.append(route_obj)

    return VaultConfig(vault_path=vault_path, routes=routes)
