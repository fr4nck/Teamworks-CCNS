param(
    [Parameter(Mandatory = $true)]
    [string]$DumpPath
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $Here 'compose.yml'
$EnvFile = Join-Path $Here '.env'
$StartScript = Join-Path $Here 'start.ps1'

$DumpPath = (Resolve-Path $DumpPath).Path
if (-not (Test-Path $DumpPath -PathType Leaf)) { throw "Dump introuvable : $DumpPath" }
if (-not (Test-Path $EnvFile)) { throw "Configuration absente : $EnvFile" }

& $StartScript
if ($LASTEXITCODE -ne 0) { throw 'Impossible de démarrer la base de développement.' }

$ContainerDump = '/tmp/teamworks-import.sql'
Write-Host 'Copie temporaire du dump dans le conteneur...' -ForegroundColor Cyan
& docker cp $DumpPath "teamworks-mysql55:$ContainerDump"
if ($LASTEXITCODE -ne 0) { throw 'Échec de docker cp.' }

try {
    Write-Host 'Import SQL en cours...' -ForegroundColor Cyan
    & docker compose --env-file $EnvFile -f $ComposeFile exec -T mysql55 sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" < /tmp/teamworks-import.sql'
    if ($LASTEXITCODE -ne 0) { throw 'Import SQL en échec.' }

    $count = & docker compose --env-file $EnvFile -f $ComposeFile exec -T mysql55 sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" -Nse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE();"'
    if ($LASTEXITCODE -ne 0) { throw 'Import terminé mais contrôle final impossible.' }
    Write-Host "Import terminé : $count tables détectées." -ForegroundColor Green
}
finally {
    & docker compose --env-file $EnvFile -f $ComposeFile exec -T mysql55 rm -f $ContainerDump | Out-Null
}
