"""
Utility package for exporting Obsidian notes into Notion databases.

The tooling now focuses on exporting a specific markdown file that is passed
in explicitly (e.g., from an Obsidian shell command). Routing into different
databases is still handled via configuration rather than by crawling a vault.
"""
__all__ = [
    "config",
    "notion_client",
    "parser",
    "exporter",
]
