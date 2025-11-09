from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Set, Tuple

from .config import DatabaseRoute, EnvConfig
from .notion_client import NotionClient
from .parser import ObsidianNote


def normalize_notion_date(raw_value: str) -> str:
    cleaned = raw_value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1]

    for candidate in (cleaned, cleaned.replace(" ", "T", 1)):
        try:
            dt = datetime.fromisoformat(candidate)
            return dt.isoformat()
        except ValueError:
            continue
    return raw_value


def resolve_relations(
    client: NotionClient,
    database_id: str,
    names: Sequence[str],
    *,
    title_property: str = "Name",
) -> Tuple[List[Dict[str, str]], List[str]]:
    relations: List[Dict[str, str]] = []
    missing: List[str] = []

    for name in names:
        page_ids = client.query_database_by_title(database_id, name, property_name=title_property)
        if page_ids:
            relations.append({"id": page_ids[0]})
        else:
            missing.append(name)
    return relations, missing


def build_page_payload(
    note: ObsidianNote,
    database: DatabaseRoute,
    location_relations: List[Dict[str, str]],
    person_relations: List[Dict[str, str]],
    *,
    available_properties: Optional[Set[str]] = None,
) -> Dict:
    properties: Dict[str, Dict] = {
        database.properties.name: {"title": [{"type": "text", "text": {"content": note.source_name}}]},
    }

    def supports(prop_name: Optional[str]) -> bool:
        if not prop_name:
            return False
        return available_properties is None or prop_name in available_properties

    if note.date_property and supports(database.properties.date):
        properties[database.properties.date] = {"date": {"start": normalize_notion_date(note.date_property)}}

    if location_relations and supports(database.properties.location):
        properties[database.properties.location] = {"relation": location_relations}
    elif location_relations:
        print("[warn] Skipping location relation; property not in database schema.")

    if person_relations and supports(database.properties.person):
        properties[database.properties.person] = {"relation": person_relations}
    elif person_relations:
        print("[warn] Skipping person relation; property not in database schema.")

    CHUNK_SIZE = 1900

    def chunk_text(text: str) -> List[str]:
        return [text[i : i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)] or [""]

    children: List[Dict] = []
    for chunk in chunk_text(note.body):
        children.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}],
                },
            }
        )

    return {
        "parent": {"database_id": database.main_db_id},
        "properties": properties,
        "children": children,
    }


@dataclass
class ExportResult:
    note: ObsidianNote
    payload: Dict
    missing_locations: List[str]
    missing_people: List[str]
    sent: bool = False
    notion_url: Optional[str] = None


def export_note(
    note: ObsidianNote,
    env_config: EnvConfig,
    database: DatabaseRoute,
    *,
    client: Optional[NotionClient] = None,
    skip_lookups: bool = False,
    send_to_notion: bool = False,
) -> ExportResult:
    if client is None and (send_to_notion or not skip_lookups):
        client = NotionClient(env_config.token)
    elif client is None:
        # For pure dry-runs we can work without an instantiated client.
        client = None

    if skip_lookups or client is None:
        location_relations: List[Dict[str, str]] = []
        person_relations: List[Dict[str, str]] = []
        missing_locations = note.locations
        missing_people = note.people
    else:
        location_db = database.location_db_id or env_config.default_location_db_id
        person_db = database.person_db_id or env_config.default_person_db_id

        if location_db:
            location_relations, missing_locations = resolve_relations(client, location_db, note.locations)
        else:
            location_relations, missing_locations = [], note.locations

        if person_db:
            person_relations, missing_people = resolve_relations(client, person_db, note.people)
        else:
            person_relations, missing_people = [], note.people

    if not skip_lookups and client is not None:
        try:
            available_properties = client.get_database_property_names(database.main_db_id)
        except Exception:
            available_properties = None
    else:
        available_properties = None

    payload = build_page_payload(
        note,
        database,
        location_relations,
        person_relations,
        available_properties=available_properties,
    )

    response: Optional[Dict] = None
    if send_to_notion and client is not None:
        response = client.create_page(payload)

    return ExportResult(
        note=note,
        payload=payload,
        missing_locations=missing_locations,
        missing_people=missing_people,
        sent=send_to_notion and response is not None,
        notion_url=(response or {}).get("url") if response else None,
    )
