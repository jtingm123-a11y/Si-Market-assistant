param(
    [string]$OutputPath = (Join-Path $PSScriptRoot "SiMarketAssistant.exe")
)

$ErrorActionPreference = "Stop"
$sourcePath = Join-Path $PSScriptRoot "launcher.cs"
$outputDirectory = Split-Path -Parent $OutputPath

if (-not (Test-Path $sourcePath)) {
    throw "Launcher source was not found: $sourcePath"
}

New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
Add-Type -Path $sourcePath -OutputAssembly $OutputPath -OutputType ConsoleApplication

if (-not (Test-Path $OutputPath) -or (Get-Item $OutputPath).Length -eq 0) {
    throw "The launcher executable was not created correctly: $OutputPath"
}

Write-Host "Launcher created:"
Write-Host $OutputPath
