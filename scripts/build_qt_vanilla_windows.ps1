param(
    [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repositoryRoot

$entryPoint = Join-Path $repositoryRoot "poc/qt-theme/vanilla_launcher.py"
$icon = Join-Path $repositoryRoot "teamworks/Static/Images/Branding/Teamworks-CCNS.ico"
$distRoot = Join-Path $repositoryRoot "dist/qt-vanilla"
$workRoot = Join-Path $repositoryRoot "build/qt-vanilla"
$appDir = Join-Path $distRoot "Teamworks-CCNS-Qt"
$portableRoot = Join-Path $distRoot "portable"
$portableApp = Join-Path $portableRoot "Teamworks-CCNS-Qt"
$portableZip = Join-Path $distRoot ("Teamworks-CCNS-Qt-{0}-windows-x64-portable.zip" -f $Version)

foreach ($required in @($entryPoint, $icon)) {
    if (-not (Test-Path $required)) {
        throw "Fichier requis introuvable : $required"
    }
}

Remove-Item $distRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $workRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $distRoot | Out-Null
New-Item -ItemType Directory -Force -Path $workRoot | Out-Null

$arguments = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onedir",
    "--contents-directory", ".",
    "--windowed",
    "--name", "Teamworks-CCNS-Qt",
    "--distpath", $distRoot,
    "--workpath", $workRoot,
    "--specpath", $workRoot,
    "--paths", $repositoryRoot,
    "--paths", (Join-Path $repositoryRoot "teamworks"),
    "--paths", (Join-Path $repositoryRoot "poc/qt-theme"),
    "--icon", $icon,
    "--add-data", ((Join-Path $repositoryRoot "teamworks/Static") + ";Static"),
    "--hidden-import", "GestionDB",
    "--hidden-import", "Chemins",
    "--hidden-import", "mysql.connector",
    "--exclude-module", "wx",
    "--exclude-module", "wxPython",
    $entryPoint
)

& python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller Qt a échoué avec le code $LASTEXITCODE."
}

$exe = Join-Path $appDir "Teamworks-CCNS-Qt.exe"
if (-not (Test-Path $exe)) {
    throw "Exécutable Qt introuvable après build : $exe"
}

Set-Content -Path (Join-Path $appDir "VANILLA_VERSION.txt") -Value $Version -Encoding UTF8

$wxArtifacts = Get-ChildItem -Path $appDir -Recurse -Force | Where-Object {
    $_.Name -eq "wx" -or
    $_.Name -eq "wxPython" -or
    $_.Name -like "wx*.pyd"
}
if ($wxArtifacts) {
    $names = ($wxArtifacts | ForEach-Object { $_.FullName }) -join [Environment]::NewLine
    throw "Le build Qt embarque encore des artefacts wx interdits :$([Environment]::NewLine)$names"
}

if (-not (Test-Path (Join-Path $appDir "PySide6"))) {
    throw "Le runtime PySide6 n'a pas été collecté."
}
if (-not (Test-Path (Join-Path $appDir "Static/Documents"))) {
    throw "Les modèles Documents RH n'ont pas été collectés."
}

New-Item -ItemType Directory -Force -Path $portableRoot | Out-Null
Copy-Item -Path $appDir -Destination $portableApp -Recurse
New-Item -ItemType Directory -Force -Path (Join-Path $portableApp "Portable") | Out-Null

Remove-Item $portableZip -Force -ErrorAction SilentlyContinue
Compress-Archive -Path $portableApp -DestinationPath $portableZip -CompressionLevel Optimal

Write-Host "Qt Vanilla build : $appDir"
Write-Host "Portable : $portableZip"
