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
- PROJECTS_VAULT_PATH = folder path containing project notes for "Notion name" overrides

2. Add "Shell commands" obsidian plug-in
3. Add the "obsidian_shell_command.ps1" script as a new shell command for the plug-in
4. in the options for the shell command, {{file_path:absolute}} as a standard input for the script

Use the "run_note_export.ps1" script to trouble shoot

Each run also appends to `export.log` (repo root) with timestamps, missing relation notes, and Notion page URLs so you can audit what happened later. Pass `--debug-log` (already wired into the helper scripts) if you need full payload/response dumps in `export.debug.log`.

When `PROJECTS_VAULT_PATH` is set, project wiki links are resolved by opening the matching `.md` file, reading its front-matter `Notion name`, and using that value for Notion lookups. If the file or property is missing, the exporter falls back to the literal `[[Project]]` text.

### Need to Know
- .md files should be formatted like the `example_note.md` file include
- we do not find a matching property in notion for the obsidian links a popup warning will show
    - if this happens, manually add them to notion

### To Do
- error message when notion api does not have access to dbs
- way to parse md file and keep formatting (the ## header stuff)
    - I think - each notion page contians "blocks" each block contains text.
    - maybe we read the .md file, and try to break the formatted ## stuff into blocks, and apply the formatting to a json property
- handle the "Long name" property for organizations
- how to handle matching the names of related properties
    - currently, is there is no match, that property is not added (no new page made)
    - do we want to create pages in the related dbs if they do not exist
    - do we add a property to the obsidian relations that has the db_id for the proper notion db?
        - update -- added a "Notion name" property to my projects in obsidian. for now this is used as a lookup to get the matching notion name
        - example
            1. read md file we will export
            2. read one of the linked projects (ex. 2025 - Client LF)
            3. then go to the 2025 - Client LF page and read some property called "notion_db_id"
            4. then use that "notion_db_id" to create the related property in the notion database
- how to handle cases where i export a .md file, then update that .md file one week later
- figure out how obsidian-shellcommands can pass more arguments 
- learn obsidian-shellcommands better
    - it has variables that it can pass like {{yaml_content}} - may be easier than parsing the .md file
- it is set up to use a lookup to get a "notion name" for the projects. some may rather not use a lookup and keep their obsidian vault "synced" up with notion, if this is the case, they might want some sort of user input in a config file to determine if we should use a lookup or not. 


Pass `--debug-log` to capture full payload/response data in `export.debug.log` when troubleshooting.
- currently treated as hardcoded lines in run_note_export.ps1
