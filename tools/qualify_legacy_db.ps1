$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
Set-Location $repository
$project = 'tw-db-proof-' + [Guid]::NewGuid().ToString('N').Substring(0, 12)
$container = $project + '-mysql55'
$proofRoot = Join-Path ([IO.Path]::GetTempPath()) $project
New-Item -ItemType Directory -Path $proofRoot | Out-Null
$utf8 = New-Object System.Text.UTF8Encoding($false)
$utf8Bom = New-Object System.Text.UTF8Encoding($true)
Copy-Item -LiteralPath (Join-Path $repository 'dev/db') -Destination $proofRoot -Recurse
$dbDir = Join-Path $proofRoot 'db'
$compose = Join-Path $dbDir 'compose.yml'
$envFile = Join-Path $dbDir '.env'

# Use a separate Compose project, container and volume. Never run the repository reset script.
$composeText = [IO.File]::ReadAllText($compose)
if (-not $composeText.Contains('name: teamworks-dev')) { throw 'Unexpected Compose project.' }
$composeText = $composeText.Replace('name: teamworks-dev', "name: $project").Replace('teamworks-mysql55', $container)
[IO.File]::WriteAllText($compose, $composeText, $utf8)
foreach ($script in Get-ChildItem -LiteralPath $dbDir -Filter '*.ps1') {
    $scriptText = [IO.File]::ReadAllText($script.FullName).Replace('teamworks-mysql55', $container)
    [IO.File]::WriteAllText($script.FullName, $scriptText, $utf8Bom)
}
$listener = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback, 0)
$listener.Start()
$port = $listener.LocalEndpoint.Port
$listener.Stop()
$rootPassword = [Guid]::NewGuid().ToString('N')
$userPassword = [Guid]::NewGuid().ToString('N')
$configuration = @(
    "TEAMWORKS_DB_ROOT_PASSWORD=$rootPassword"
    'TEAMWORKS_DB_NAME=teamworks_proof'
    'TEAMWORKS_DB_USER=teamworks'
    "TEAMWORKS_DB_PASSWORD=$userPassword"
    "TEAMWORKS_DB_PORT=$port"
) -join "`n"
[IO.File]::WriteAllText($envFile, $configuration + "`n", $utf8)

$dumpPath = Join-Path $proofRoot 'synthetic.sql'
$dump = @'
CREATE TABLE personnes (IDpersonne INT PRIMARY KEY, nom VARCHAR(80), prenom VARCHAR(80));
INSERT INTO personnes VALUES (1, 'SyntheticName', 'SyntheticGiven');
CREATE TABLE coordonnees (IDcoord INT PRIMARY KEY, categorie VARCHAR(30), texte VARCHAR(120));
INSERT INTO coordonnees VALUES (1, 'mail', 'synthetic@example.invalid');
'@
[IO.File]::WriteAllText($dumpPath, $dump, $utf8)

function Invoke-ProofSql {
    param([string]$Sql)
    $result = $Sql | & docker compose --env-file $envFile -f $compose exec -T mysql55 sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" -N -B'
    if ($LASTEXITCODE -ne 0) { throw 'Proof SQL failed.' }
    return $result
}

try {
    docker compose --env-file $envFile -f $compose config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Proof Compose invalid.' }
    & (Join-Path $dbDir 'import.ps1') -DumpPath $dumpPath
    $version = Invoke-ProofSql 'SELECT VERSION();'
    if ($version -notmatch '^5\.5\.62') { throw "Unexpected server version: $version" }
    $count = Invoke-ProofSql 'SELECT COUNT(*) FROM personnes;'
    if ("$count".Trim() -ne '1') { throw 'Synthetic import failed.' }
    Write-Output 'PROOF_IMPORT: SUCCESS'

    & (Join-Path $dbDir 'anonymize.ps1') -Force
    $actual = Invoke-ProofSql "SELECT CONCAT(nom, '|', prenom, '|', texte) FROM personnes CROSS JOIN coordonnees;"
    if ("$actual".Trim() -ne 'PERSONNE_000001|Prenom_000001|contact1@example.invalid') {
        throw 'Anonymization without optional column failed.'
    }
    Write-Output 'PROOF_ANON_WITHOUT_INTITULE: SUCCESS'

    Invoke-ProofSql "ALTER TABLE coordonnees ADD intitule VARCHAR(80); UPDATE coordonnees SET intitule='Synthetic label';" | Out-Null
    & (Join-Path $dbDir 'anonymize.ps1') -Force
    $actual = Invoke-ProofSql 'SELECT intitule FROM coordonnees;'
    if ("$actual".Trim() -ne 'Coordonnee test') { throw 'Optional column anonymization failed.' }
    Write-Output 'PROOF_ANON_WITH_INTITULE: SUCCESS'

    & (Join-Path $dbDir 'reset.ps1') -Force
    $count = Invoke-ProofSql 'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE();'
    if ("$count".Trim() -ne '0') { throw 'Isolated reset failed.' }
    Write-Output 'PROOF_RESET: SUCCESS'
    Write-Output 'TEAMWORKS_LEGACY_DB_PROOF: SUCCESS'
}
finally {
    docker compose --env-file $envFile -f $compose down -v --remove-orphans
    if ($LASTEXITCODE -ne 0) { throw "Proof cleanup failed. Project: $project" }
    Write-Output "Proof files retained locally: $proofRoot"
}
