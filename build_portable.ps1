param(
    [string]$PythonVersion = "3.13.15"
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$buildRoot = Join-Path $projectRoot "build\portable"
$distRoot = Join-Path $projectRoot "dist"
$archivePath = Join-Path $distRoot "A-Stock-Assistant-Windows-x64.zip"
$runtimeRoot = Join-Path $buildRoot "runtime"
$versionParts = $PythonVersion.Split(".")
$buildId = [Guid]::NewGuid().ToString("N")

if ($versionParts.Count -lt 2) {
    throw "PythonVersion must be a full version, for example 3.13.15."
}

$pythonTag = "python{0}{1}" -f $versionParts[0], $versionParts[1]
$embedArchive = Join-Path $env:TEMP "$pythonTag-$buildId-embed-amd64.zip"
$getPipScript = Join-Path $env:TEMP "get-pip-$buildId.py"
$embedUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$getPipUrl = "https://bootstrap.pypa.io/get-pip.py"

Write-Host "Downloading portable Python $PythonVersion..."
Invoke-WebRequest -Uri $embedUrl -OutFile $embedArchive -UseBasicParsing
Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipScript -UseBasicParsing

if (Test-Path $buildRoot) {
    Remove-Item -LiteralPath $buildRoot -Recurse -Force
}
if (Test-Path $archivePath) {
    Remove-Item -LiteralPath $archivePath -Force
}
New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
New-Item -ItemType Directory -Path $distRoot -Force | Out-Null
Expand-Archive -LiteralPath $embedArchive -DestinationPath $runtimeRoot -Force

$pthFile = Join-Path $runtimeRoot "$pythonTag._pth"
if (-not (Test-Path $pthFile)) {
    throw "Portable Python configuration file was not found: $pthFile"
}
@(
    "$pythonTag.zip"
    "."
    "Lib\site-packages"
    "import site"
) | Set-Content -Path $pthFile -Encoding ASCII

$sitePackages = Join-Path $runtimeRoot "Lib\site-packages"
New-Item -ItemType Directory -Path $sitePackages -Force | Out-Null
Write-Host "Installing dependencies into the portable runtime. This is a one-time build step..."
& (Join-Path $runtimeRoot "python.exe") $getPipScript --no-warn-script-location
if ($LASTEXITCODE -ne 0) {
    throw "Could not bootstrap pip into the portable Python runtime."
}

$runtimeRequirements = Join-Path $buildRoot "requirements-runtime.txt"
$runtimeDependencyLines = Get-Content (Join-Path $projectRoot "requirements.txt") |
    Where-Object { $_.Trim() -and $_ -notmatch "^\s*pytest\s*[<=>~!]" }
$runtimeDependencyLines | Set-Content -Path $runtimeRequirements -Encoding ASCII
& (Join-Path $runtimeRoot "python.exe") -m pip install --disable-pip-version-check --no-warn-script-location -r $runtimeRequirements
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed. Review the pip output and retry the build."
}

& (Join-Path $runtimeRoot "python.exe") -c "import streamlit, pandas, numpy, akshare, plotly"
if ($LASTEXITCODE -ne 0) {
    throw "The portable runtime failed its dependency import check."
}

$pipPackage = Join-Path $sitePackages "pip"
if (Test-Path $pipPackage) {
    Remove-Item -LiteralPath $pipPackage -Recurse -Force
}
Get-ChildItem -Path $sitePackages -Directory -Filter "pip-*.dist-info" |
    Remove-Item -Recurse -Force
Remove-Item -LiteralPath $embedArchive, $getPipScript -Force -ErrorAction SilentlyContinue

Copy-Item -LiteralPath (Join-Path $projectRoot "app.py") -Destination $buildRoot
foreach ($directory in @("pages", "src", "config")) {
    Copy-Item -LiteralPath (Join-Path $projectRoot $directory) -Destination $buildRoot -Recurse
}
New-Item -ItemType Directory -Path (Join-Path $buildRoot "data\exports") -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot "run_portable.bat") -Destination $buildRoot
Copy-Item -LiteralPath (Join-Path $projectRoot "PORTABLE_README.txt") -Destination $buildRoot

Remove-Item -LiteralPath $runtimeRequirements -Force
Compress-Archive -Path (Join-Path $buildRoot "*") -DestinationPath $archivePath -CompressionLevel Optimal
if (-not (Test-Path $archivePath) -or (Get-Item $archivePath).Length -eq 0) {
    throw "The portable ZIP was not created correctly."
}
Remove-Item -LiteralPath $buildRoot -Recurse -Force
Write-Host ""
Write-Host "Portable package created:"
Write-Host $archivePath
Write-Host "Upload this ZIP as a GitHub Release asset. Do not commit the generated ZIP to the source repository."
