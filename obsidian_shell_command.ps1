<#
.SYNOPSIS
    Convenience wrapper that forwards a note path to run_note_export.ps1 and forces --send.

.DESCRIPTION
    Accepts a single argument (absolute markdown path) and invokes run_note_export.ps1
    with the same path plus the --send flag so callers do not have to manage CLI switches.
#>
[CmdletBinding(PositionalBinding = $true)] # allow simple positional invocation for Templater/Shell Commands
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$NotePath
)

Set-StrictMode -Version Latest  # catch mistakes early (e.g., undefined variables)
$ErrorActionPreference = "Stop" # abort immediately on any failure

$rootScript = Join-Path -Path (Split-Path -Parent $PSCommandPath) -ChildPath "run_note_export.ps1" # reuse the main helper

if (-not (Test-Path $rootScript)) {
    throw "Cannot locate base exporter script at $rootScript"
}

if (-not [System.IO.Path]::IsPathRooted($NotePath)) {
    throw "Provide the full markdown path. Received relative path: $NotePath"
}

$resolvedNote = (Resolve-Path $NotePath).Path
& $rootScript $resolvedNote "--send" # always include --send so Obsidian button creates the page
