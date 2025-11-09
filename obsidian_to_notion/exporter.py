from __future__ import annotations

import json
import logging
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
    client: NotionClient
    ,database_id: str
    ,names: Sequence[str]
    ,*
    ,title_property: str = "Name"
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
    note: ObsidianNote
    ,database: DatabaseRoute

    ,organizations_relations: List[Dict[str, str]]
    ,projects_relations: List[Dict[str, str]]
    ,participants_relations: List[Dict[str, str]]
    
    ,*
    ,available_properties: Optional[Set[str]] = None
) -> Dict:
    properties: Dict[str, Dict] = {database.properties.name: {"title": [{"type": "text", "text": {"content": note.source_name}}]}}

    def supports(prop_name: Optional[str]) -> bool:
        if not prop_name:
            return False
        return available_properties is None or prop_name in available_properties

    if note.date_property and supports(database.properties.date):
        properties[database.properties.date] = {"date": {"start": normalize_notion_date(note.date_property)}}

    # Organizations
    if organizations_relations and supports(database.properties.organizations):
        properties[database.properties.organizations] = {"relation": organizations_relations}
    elif organizations_relations:
        print("[warn] Skipping organizations relation: property not in database schema.")
    
    # Projects
    if projects_relations and supports(database.properties.projects):
        properties[database.properties.projects] = {"relation": projects_relations}
    elif projects_relations:
        print("[warn] Skipping projects relation: property noy in database schema.")

    # Participants
    if participants_relations and supports(database.properties.participants):
        properties[database.properties.participants] = {"relation": participants_relations}
    elif participants_relations:
        print("[warn] Skipping participants relation: property not in database schema.")


    CHUNK_SIZE = 1900

    def chunk_text(text: str) -> List[str]:
        return [text[i : i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)] or [""]

    children: List[Dict] = []
    for chunk in chunk_text(note.body):
        children.append(
            {
                "object": "block"
                ,"type": "paragraph"
                ,"paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            }
        )

    return {
        "parent": {"database_id": database.resolved_db_id}
        ,"properties": properties
        ,"children": children
    }


@dataclass
class ExportResult:
    note: ObsidianNote
    payload: Dict

    missing_organizations: List[str]
    missing_projects: List[str]
    missing_participants: List[str]

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
    debug_logger: Optional[logging.Logger] = None,
) -> ExportResult:
    if client is None and (send_to_notion or not skip_lookups):
        client = NotionClient(env_config.token)
    elif client is None:
        # For pure dry-runs we can work without an instantiated client.
        client = None

    if skip_lookups or client is None:
        organizations_relations: List[Dict[str, str]] = []
        projects_relations: List[Dict[str, str]] = []
        participants_relations: List[Dict[str, str]] = []

        missing_organizations = note.organizations
        missing_projects = note.projects
        missing_participants = note.participants

    else:
        organizations_db = database.organizations_db_id or env_config.default_organizations_db_id
        projects_db = database.projects_db_id or env_config.default_projects_db_id
        participants_db = database.participants_db_id or env_config.default_participants_db_id

        if organizations_db:
            organizations_relations, missing_organizations = resolve_relations(client, organizations_db, note.organizations)
        else:
            organizations_relations, missing_organizations = [], note.organizations

        if projects_db:
            projects_relations, missing_projects = resolve_relations(client, projects_db, note.projects)
        else:
            projects_relations, missing_projects = [], note.projects

        if participants_db:
            participants_relations, missing_participants = resolve_relations(client, participants_db, note.participants)
        else:
            participants_relations, missing_participants = [], note.participants

    if not skip_lookups and client is not None:
        try:
            available_properties = client.get_database_property_names(database.resolved_db_id)
        except Exception:
            available_properties = None
    else:
        available_properties = None

    payload = build_page_payload(
        note
        ,database
        
        ,organizations_relations
        ,projects_relations
        ,participants_relations
        
        ,available_properties=available_properties
    )

    response: Optional[Dict] = None
    if send_to_notion and client is not None:
        if debug_logger:
            debug_logger.info("Sending payload for %s:\n%s", note.path, json.dumps(payload, indent=2))
        response = client.create_page(payload)
        if debug_logger:
            debug_logger.info("Response for %s:\n%s", note.path, json.dumps(response, indent=2))

    return ExportResult(
        note=note
        ,payload=payload
        
        ,missing_organizations=missing_organizations
        ,missing_projects=missing_projects
        ,missing_participants=missing_participants
        
        ,sent=send_to_notion and response is not None
        ,notion_url=(response or {}).get("url") if response else None
    )
