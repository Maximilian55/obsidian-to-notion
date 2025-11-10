from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or malformed."""


@dataclass
class EnvConfig:
    '''Expected variables in .env file'''

    token: str
    default_meetings_db_id: Optional[str] = None
    default_notes_db_id: Optional[str] = None
    default_organizations_db_id: Optional[str] = None
    default_projects_db_id: Optional[str] = None
    default_participants_db_id: Optional[str] = None
    meetings_vault_path: Optional[Path] = None
    notes_vault_path: Optional[Path] = None
    projects_vault_path: Optional[Path] = None

@dataclass
class PropertyMapping:
    '''Name of properties in target database'''

    name: str = "Name"
    date: Optional[str] = "Date"
    organizations: Optional[str] = "Organization"
    projects: Optional[str] = "Projects"
    participants: Optional[str] = "Participants"


@dataclass
class DatabaseRoute:
    '''Routing info for notion import'''

    target_db_id: str
    organizations_db_id: Optional[str] = None
    projects_db_id: Optional[str] = None
    participants_db_id: Optional[str] = None
    properties: PropertyMapping = field(default_factory=PropertyMapping)

    @property
    def resolved_db_id(self) -> str:
        return self.target_db_id



def load_env_file(path: Path) -> EnvConfig:
    """Parse the provided .env file and return a structured EnvConfig."""
    
    raw: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        raw[key.strip()] = value.strip().strip('"').strip("'")

    try:
        meetings_vault = raw.get("MEETINGS_VAULT_PATH")
        notes_vault = raw.get("NOTES_VAULT_PATH")
        projects_vault = raw.get("PROJECTS_VAULT_PATH")
        meetings_db = raw.get("MEETINGS_DB_ID")
        notes_db = raw.get("NOTES_DB_ID")
        if not meetings_db and not notes_db:
            raise ConfigurationError("Provide at least MEETINGS_DB_ID or NOTES_DB_ID in .env")

        return EnvConfig(
            token=raw["NOTION_TOKEN"]
            ,default_meetings_db_id=meetings_db
            ,default_notes_db_id=notes_db
            ,default_organizations_db_id=raw["ORGANIZATIONS_DB_ID"]
            ,default_projects_db_id=raw["PROJECTS_DB_ID"]
            ,default_participants_db_id=raw["PARTICIPANTS_DB_ID"]
            ,meetings_vault_path=Path(meetings_vault).expanduser() if meetings_vault else None
            ,notes_vault_path=Path(notes_vault).expanduser() if notes_vault else None
            ,projects_vault_path=Path(projects_vault).expanduser() if projects_vault else None
        )
    except KeyError as missing:
        raise ConfigurationError(f"Missing env var: {missing.args[0]}") from missing
