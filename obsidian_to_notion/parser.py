from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


BRACKETS_RE = re.compile(r"\[\[([^\]]+)\]\]")


@dataclass
class ObsidianNote:
    front_matter: Dict[str, str]
    metadata_section: str
    body: str
    locations: List[str]
    people: List[str]
    source_name: str
    path: Path

    @property
    def date_property(self) -> Optional[str]:
        return self.front_matter.get("date")


def parse_front_matter_and_remainder(text: str) -> Tuple[Dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text

    closing_idx = text.find("\n---", 3)
    if closing_idx == -1:
        return {}, text

    front_matter_chunk = text[3:closing_idx].strip()
    remainder = text[closing_idx + 4 :].lstrip("\r\n")

    data: Dict[str, str] = {}
    for raw_line in front_matter_chunk.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data, remainder


def split_metadata_and_body(text: str) -> Tuple[str, str]:
    lines = text.splitlines()
    metadata_lines: List[str] = []
    for idx, line in enumerate(lines):
        if line.strip() == "---":
            metadata = "\n".join(metadata_lines).strip("\r\n")
            body = "\n".join(lines[idx + 1 :]).lstrip("\r\n")
            return metadata, body
        metadata_lines.append(line)
    metadata = "\n".join(metadata_lines).strip("\r\n")
    return metadata, ""


def extract_bracket_links(text: str) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for match in BRACKETS_RE.finditer(text):
        value = match.group(1).strip()
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def parse_note(path: Path) -> ObsidianNote:
    text = path.read_text(encoding="utf-8")
    front_matter, remainder = parse_front_matter_and_remainder(text)
    metadata_section, notion_body = split_metadata_and_body(remainder)

    lines = metadata_section.splitlines()
    locations: List[str] = []
    people: List[str] = []
    collecting_people = False

    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("**location**::"):
            locations = extract_bracket_links(stripped)
            collecting_people = False
            continue

        if stripped.lower().startswith("**person**::"):
            people.extend(extract_bracket_links(stripped))
            collecting_people = True
            continue

        if collecting_people:
            if not stripped or not stripped.startswith("-"):
                collecting_people = False
                continue
            people.extend(extract_bracket_links(stripped))

    return ObsidianNote(
        front_matter=front_matter,
        metadata_section=metadata_section,
        body=notion_body,
        locations=locations,
        people=people,
        source_name=path.stem,
        path=path,
    )
