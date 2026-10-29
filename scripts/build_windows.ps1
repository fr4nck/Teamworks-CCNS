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

# Conserver la licence à la racine du paquet : Chemins.GetMainPath()
# utilise le répertoire de l'exécutable lorsque l'application est figée.
$package = Join-Path $repositoryRoot 'dist/Teamworks-CCNS'
Copy-Item -LiteralPath (Join-Path $repositoryRoot 'teamworks/Licence.txt') `
    -Destination (Join-Path $package 'Licence.txt') -Force -ErrorAction Stop
Copy-Item -LiteralPath (Join-Path $repositoryRoot 'teamworks/Versions.txt') `
    -Destination (Join-Path $package 'Versions.txt') -Force -ErrorAction Stop
