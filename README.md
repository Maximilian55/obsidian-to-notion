## Obsidian → Notion Exporter

### Components

- `obsidian_to_notion/parser.py` - pulls metadata/body out of the markdown file.
- `obsidian_to_notion/notion_client.py` - tiny wrapper around the Notion REST API.
- `obsidian_to_notion/exporter.py` - builds the Notion payload (with body chunking) and sends it.
- `obsidian_to_notion/cli.py` - command-line entry point that wires everything together.

### Usage

1. Create `.env` file and fill in your Notion integration token plus database ids.
Example:
- NOTION_TOKEN = notion API token
- MEETINGS_DB_ID = notion database_id
- ORGANIZATIONS_DB_ID = notion database_id
- MEETINGS_VAULT_PATH = folder path of obsidian meetings
- NOTES_VAULT_PATH = folder path of obsidian notes

2. Add "Shell commands" obsidian plug-in
3. Add the "obsidian_shell_command.ps1" script as a new shell command for the plug-in
4. in the options for the shell command, {{file_path:absolute}} as a standard input for the script

Use the "run_note_export.ps1" script to trouble shoot

### To Do
- error message when notion api does not have access to dbs
- way to parse md file and keep formatting (the ## header stuff)
    - I think - each notion page contians "blocks" each block contains text.
    - maybe we read the .md file, and try to break the formatted ## stuff into blocks, and apply the formatting to a json property
- handle the "Long name" property for organizations
- how to handle matching the names of related properties
    - do we want to create pages in the related dbs if they do not exist
    - do we add a property to the obsidian relations that has the db_id for the proper notion db?
        - example
            1. read md file we will export
            2. read one of the linked projects (ex. 2025 - Client LF)
            3. then go to the 2025 - Client LF page and read some property called "notion_db_id"
            4. then use that "notion_db_id" to create the related property in the notion database
- how to handle cases where i export a .md file, then update that .md file one week later
- add log




