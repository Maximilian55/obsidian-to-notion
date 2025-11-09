<#
.SYNOPSIS
    Bootstraps the venv and runs the Obsidian-to-Notion exporter for a single note.

.DESCRIPTION
    Accepts the markdown path as the first argument and forwards any additional
    CLI flags directly to export_note_to_notion.py once the virtual environment
    has been created (or reused) and dependencies installed.
#>
[CmdletBinding(PositionalBinding = $true)]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$NotePath,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ForwardedArgs
)

Set-StrictMode -Version Latest  # catch undeclared variables / typos early
$ErrorActionPreference = "Stop" # fail fast on any error instead of continuing silently

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8 # ensure PowerShell emits UTF-8 (for Notion payload printing)
$env:PYTHONIOENCODING = "utf-8" # make Python print/encode logs in UTF-8 too

$repoRoot = Split-Path -Parent $PSCommandPath # repo root derived from script path
$venvPath = Join-Path $repoRoot ".venv"       # virtualenv lives in .venv by convention
$runningOnWindows = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform(
    [System.Runtime.InteropServices.OSPlatform]::Windows
)
$pythonSubPath = if ($runningOnWindows) { "Scripts/python.exe" } else { "bin/python" }
$pythonExe = Join-Path $venvPath $pythonSubPath

function Invoke-SystemPython {
    param([string[]]$PyArgs)

    $candidates = @("python", "py") # use whichever launcher is on PATH
    foreach ($cmd in $candidates) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            & $cmd @PyArgs
            return
        }
    }

    throw "Could not locate a system Python interpreter ('python' or 'py')."
}

Push-Location $repoRoot # run everything as if script is executed from repo root
try {
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating virtual environment at $venvPath" -ForegroundColor Cyan
        Invoke-SystemPython @("-m", "venv", $venvPath)
    }

    if (-not (Test-Path $pythonExe)) {
        throw "Virtual environment is missing a python executable at $pythonExe."
    }

    $requirements = Join-Path $repoRoot "requirements.txt"
    if (Test-Path $requirements) {
        Write-Host "Installing/updating dependencies from requirements.txt" -ForegroundColor Cyan
        & $pythonExe -m pip install --upgrade pip | Out-Null
        & $pythonExe -m pip install -r $requirements
    }

    $isRooted = [System.IO.Path]::IsPathRooted($NotePath)
    if (-not $isRooted) {
        throw "Provide the full markdown path. Received relative path: $NotePath"
    }
    $resolvedNote = (Resolve-Path $NotePath).Path
    $exporter = Join-Path $repoRoot "export_note_to_notion.py"

    if (-not (Test-Path $exporter)) {
        throw "Cannot locate export_note_to_notion.py at $exporter"
    }

    ## hardcoded lines to run with and without debug logging -- need to find a way for obsidian to pass more arguments

    # $argsToPass = @($resolvedNote) + ($ForwardedArgs | Where-Object { $_ -ne $null })
    $argsToPass = @($resolvedNote, "--debug-log") + ($ForwardedArgs | Where-Object { $_ -ne $null })
    Write-Host "Running exporter for $resolvedNote" -ForegroundColor Cyan

    $output = & $pythonExe $exporter @argsToPass 2>&1
    $output | ForEach-Object { Write-Host $_ }

    $exitCode = $LASTEXITCODE
    $warningLines = $output | Where-Object { $_ -match '^\u26A0' } # lines starting with ⚠

    if ($warningLines) {
        $message = ($warningLines -join "`n")
        try {
            Add-Type -AssemblyName PresentationFramework -ErrorAction Stop | Out-Null
            [System.Windows.MessageBox]::Show($message, "Notion Export Warnings") | Out-Null
        } catch {
            Write-Warning "Missing relation warnings:`n$message"
        }
    }

    if ($exitCode -ne 0) {
        throw "export_note_to_notion.py exited with code $exitCode"
    }
}
finally {
    Pop-Location
}
