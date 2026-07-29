$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repositoryRoot

$entryPoint = Join-Path $repositoryRoot 'teamworks/Teamworks.py'
if (-not (Test-Path $entryPoint)) {
    throw "Point d'entrée introuvable : $entryPoint"
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name 'Teamworks-CCNS' `
    --paths 'teamworks' `
    --add-data 'teamworks;teamworks' `
    --collect-all 'wx' `
    $entryPoint

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller a échoué avec le code $LASTEXITCODE."
}
