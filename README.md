## Obsidian → Notion Exporter

### Key pieces

- `obsidian_to_notion/parser.py` – front-matter parser + wiki-link extraction.
- `obsidian_to_notion/notion_client.py` – lightweight wrapper around the Notion REST API.
- `obsidian_to_notion/exporter.py` – turns parsed notes into Notion payloads and sends them.
- `obsidian_to_notion/cli.py` – command-line interface for exporting a single note (path supplied explicitly).

### Usage

1. Create `.env` file and fill in your Notion integration token plus database ids.
Example:
- NOTION_TOKEN = secret_token -- notion API
- MAIN_DB_ID = database_id -- id of the database that we import a file to
- LOCATION_ID = another_database_id -- id of a database for a related property
- PERSON_ID = another_database_id -- same as above

2. Add "Shell commands" obsidian plug-in
3. Add the "run_export_send.ps1" script as a new shell command for the plug-in
4. in the options for the shell command, {{file_path:absolute}} as a standard input for the script

Use the "run_export.ps1" script to trouble shoot

### To Do
- figure out how to make pass a input like --send from the shell command plug in (then remove the duplicate PS script)
- learn how to code so this thing is not 100% vibe codefs