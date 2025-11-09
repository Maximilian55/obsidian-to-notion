from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or malformed."""


@dataclass
class EnvConfig:
    token: str
    default_main_db_id: str
    # default_location_db_id: Optional[str] = None
    # default_person_db_id: Optional[str] = None

    # default_meeting_notes_db_id: str
    default_organizations_db_id: Optional[str] = None
    default_projects_db_id: Optional[str] = None
    default_participants_db_id: Optional[str] = None

@dataclass
class PropertyMapping:
    name: str = "Name"
    date: Optional[str] = "Date"
    # location: Optional[str] = "Location"
    # person: Optional[str] = "Person"

    organizations: Optional[str] = "Organizations"
    projects: Optional[str] = "Projects"
    participants: Optional[str] = "People"


@dataclass
class DatabaseRoute:
    main_db_id: str
    # location_db_id: Optional[str] = None
    # person_db_id: Optional[str] = None

    # meeting_db_id: str
    organizations_db_id: Optional[str] = None
    projects_db_id: Optional[str] = None
    participants_db_id: Optional[str] = None

    properties: PropertyMapping = field(default_factory=PropertyMapping)


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
            token=raw["NOTION_TOKEN"]
            ,default_main_db_id=raw["MAIN_DB_ID"]
            # ,default_location_db_id=raw.get("LOCATION_ID")
            # ,default_person_db_id=raw.get("PERSON_ID")

            # ,default_meeting_notes_db_id=raw["MEETING_NOTES_DB_ID"]
            ,default_organizations_db_id=raw["ORGANIZATIONS_DB_ID"]
            ,default_projects_db_id=raw["PROJECTS_DB_ID"]
            ,default_participants_db_id=raw["PARTICIPANTS_DB_ID"]
        )
    except KeyError as missing:
        raise ConfigurationError(f"Missing env var: {missing.args[0]}") from missing
