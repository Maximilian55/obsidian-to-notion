<#
.SYNOPSIS
    Convenience wrapper that forwards a note path to run_note_export.ps1 and forces --send.

.DESCRIPTION
    Accepts a single argument (absolute markdown path) and invokes run_note_export.ps1
    with the same path plus the --send flag so callers do not have to manage CLI switches.
#>
[CmdletBinding(PositionalBinding = $true)]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$NotePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$rootScript = Join-Path -Path (Split-Path -Parent $PSCommandPath) -ChildPath "run_note_export.ps1"

if (-not (Test-Path $rootScript)) {
    throw "Cannot locate base exporter script at $rootScript"
}

if (-not [System.IO.Path]::IsPathRooted($NotePath)) {
    throw "Provide the full markdown path. Received relative path: $NotePath"
}

$resolvedNote = (Resolve-Path $NotePath).Path
& $rootScript $resolvedNote "--send"
