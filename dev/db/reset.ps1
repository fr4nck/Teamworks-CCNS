param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
if (-not $Force) {
    throw 'Cette commande détruit la base Docker de développement. Relancer avec -Force.'
}

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $Here 'compose.yml'
$EnvFile = Join-Path $Here '.env'
$StartScript = Join-Path $Here 'start.ps1'

if (-not (Test-Path $EnvFile)) { throw "Configuration absente : $EnvFile" }

Write-Host 'Suppression du conteneur et du volume de développement...' -ForegroundColor Yellow
& docker compose --env-file $EnvFile -f $ComposeFile down -v --remove-orphans
if ($LASTEXITCODE -ne 0) { throw 'Échec de la remise à zéro Docker.' }

& $StartScript
