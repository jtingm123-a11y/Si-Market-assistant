$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$requirementsFile = Join-Path $PSScriptRoot "requirements.txt"
$markerFile = Join-Path $PSScriptRoot ".venv\requirements.sha256"

if (-not (Test-Path $venvPython)) {
    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pythonLauncher) {
        Write-Host "Project virtual environment not found. Creating .venv with Python Launcher..."
        & $pythonLauncher.Source -3 -m venv (Join-Path $PSScriptRoot ".venv")
    }
    else {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCommand) {
            Write-Error "Python was not found. Install Python 3.10 or newer and add it to PATH."
            exit 1
        }
        Write-Host "Project virtual environment not found. Creating .venv with python..."
        & $pythonCommand.Source -m venv (Join-Path $PSScriptRoot ".venv")
    }

    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) {
        Write-Error "Failed to create the virtual environment. Check the Python installation and retry."
        exit 1
    }
}

$requirementsHash = (Get-FileHash -Path $requirementsFile -Algorithm SHA256).Hash
$installedHash = if (Test-Path $markerFile) {
    (Get-Content -Path $markerFile -Raw).Trim()
}
else {
    ""
}

if ($installedHash -ne $requirementsHash) {
    Write-Host "Checking and installing project dependencies. First run may take a few minutes..."
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to upgrade pip. Check the network connection and retry."
        exit 1
    }

    & $venvPython -m pip install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install project dependencies. Review the error above and retry."
        exit 1
    }

    Set-Content -Path $markerFile -Value $requirementsHash -Encoding ASCII
}

Write-Host "Starting the A-share research assistant..."
& $venvPython -m streamlit run (Join-Path $PSScriptRoot "app.py") --server.headless true
if ($LASTEXITCODE -ne 0) {
    Write-Error "Streamlit exited with code $LASTEXITCODE."
    exit $LASTEXITCODE
}
