## Obsidian → Notion Exporter

### Key pieces

- `obsidian_to_notion/parser.py` - pulls metadata/body out of the markdown file.
- `obsidian_to_notion/notion_client.py` - tiny wrapper around the Notion REST API.
- `obsidian_to_notion/exporter.py` - builds the Notion payload (with body chunking) and sends it.
- `obsidian_to_notion/cli.py` - command-line entry point that wires everything together.

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
- learn how to code so this thing is not 100% vibe code
- error message when notion api does not have access to dbs
- way to parse md file and keep headers (the ## header stuff)
- decide on if we want to create pages in the related dbs if they do not exist
- handle for "Long name" property for organizations
- handle regular notes