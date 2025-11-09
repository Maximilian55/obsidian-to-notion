from __future__ import annotations

import json
from typing import Dict, List, Set

try:
    import requests
except ImportError as exc:  # pragma: no cover
    raise SystemExit("The 'requests' package is required. Install it with 'pip install requests'.") from exc


NOTION_VERSION = "2022-06-28"


class NotionClient:
    def __init__(self, token: str) -> None:
        """Initialize a session configured with the integration token."""

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}"
                ,"Notion-Version": NOTION_VERSION
                ,"Content-Type": "application/json"
            }
        )

    def query_database_by_title(self, database_id: str, title: str, property_name: str = "Name") -> List[str]:
        """Return Notion page IDs whose title property matches the supplied text."""

        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        payload = {
            "filter": {"property": property_name, "title": {"equals": title}}
            ,"page_size": 5
        }
        response = self.session.post(url, data=json.dumps(payload))
        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            print(f"[error] Notion query failed: {response.text}")
            raise err
        data = response.json()
        return [page["id"] for page in data.get("results", [])]

    def create_page(self, payload: Dict) -> Dict:
        """Create a page via the Notion API and return the response body."""

        url = "https://api.notion.com/v1/pages"
        response = self.session.post(url, data=json.dumps(payload))
        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            print(f"[error] Notion create failed: {response.text}")
            raise err
        return response.json()

    def fetch_database(self, database_id: str) -> Dict:
        """Fetch the schema for a Notion database."""

        url = f"https://api.notion.com/v1/databases/{database_id}"
        response = self.session.get(url)
        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            print(f"[error] Notion fetch database failed: {response.text}")
            raise err
        return response.json()

    def get_database_property_names(self, database_id: str) -> Set[str]:
        """Return the set of property names defined on a database."""
        
        data = self.fetch_database(database_id)
        return set(data.get("properties", {}).keys())
