param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
if (-not $Force) {
    throw 'Anonymisation destructive de la copie Docker. Relancer avec -Force après avoir vérifié que la cible est bien la base de développement.'
}

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $Here 'compose.yml'
$EnvFile = Join-Path $Here '.env'
$ReportFile = Join-Path $Here 'anonymization-report.txt'

if (-not (Test-Path $EnvFile)) { throw "Configuration absente : $EnvFile" }
if (-not (docker ps --format '{{.Names}}' | Select-String -SimpleMatch 'teamworks-mysql55')) {
    throw 'Le conteneur teamworks-mysql55 ne tourne pas.'
}

function Invoke-MySql {
    param([Parameter(Mandatory = $true)][string]$Sql)
    $result = $Sql | & docker compose --env-file $EnvFile -f $ComposeFile exec -T mysql55 sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" -N -B'
    if ($LASTEXITCODE -ne 0) { throw "Échec SQL : $Sql" }
    return $result
}

function Get-Columns {
    param([Parameter(Mandatory = $true)][string]$Table)
    $sql = "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='$Table' ORDER BY ORDINAL_POSITION;"
    return @(Invoke-MySql $sql)
}

function Update-IfPresent {
    param(
        [Parameter(Mandatory = $true)][string]$Table,
        [Parameter(Mandatory = $true)][hashtable]$Assignments
    )
    $columns = @(Get-Columns $Table)
    if ($columns.Count -eq 0) {
        Write-Host "Table absente, ignorée : $Table" -ForegroundColor DarkGray
        return
    }
    $parts = @()
    foreach ($column in $Assignments.Keys) {
        if ($columns -contains $column) {
            $parts += "$column = $($Assignments[$column])"
        }
    }
    if ($parts.Count -eq 0) { return }
    Invoke-MySql ("UPDATE $Table SET " + ($parts -join ', ') + ';') | Out-Null
    Write-Host "Anonymisé : $Table" -ForegroundColor Green
}

Write-Host 'Anonymisation de la copie Docker uniquement...' -ForegroundColor Cyan

Update-IfPresent 'personnes' ([ordered]@{
    nom          = "CONCAT('PERSONNE_', LPAD(IDpersonne, 6, '0'))"
    nom_jfille   = "CASE WHEN nom_jfille IS NULL OR nom_jfille='' THEN nom_jfille ELSE CONCAT('NOM_', LPAD(IDpersonne, 6, '0')) END"
    prenom       = "CONCAT('Prenom_', LPAD(IDpersonne, 6, '0'))"
    date_naiss   = "CASE WHEN date_naiss IS NULL THEN NULL ELSE STR_TO_DATE(CONCAT(YEAR(date_naiss), '-07-01'), '%Y-%m-%d') END"
    cp_naiss     = '35000'
    ville_naiss  = "'VILLE_TEST'"
    num_secu     = "''"
    adresse_resid= "CONCAT('Adresse test ', IDpersonne)"
    cp_resid     = '35000'
    ville_resid  = "'VILLE_TEST'"
    memo         = "''"
    cadre_photo  = "''"
    texte_photo  = "''"
})

Update-IfPresent 'candidats' ([ordered]@{
    nom          = "CONCAT('CANDIDAT_', LPAD(IDcandidat, 6, '0'))"
    prenom       = "CONCAT('Prenom_', LPAD(IDcandidat, 6, '0'))"
    date_naiss   = "CASE WHEN date_naiss IS NULL THEN NULL ELSE STR_TO_DATE(CONCAT(YEAR(date_naiss), '-07-01'), '%Y-%m-%d') END"
    adresse_resid= "CONCAT('Adresse test ', IDcandidat)"
    cp_resid     = '35000'
    ville_resid  = "'VILLE_TEST'"
    memo         = "''"
})

foreach ($table in @('coordonnees', 'coords_candidats')) {
    $columns = @(Get-Columns $table)
    if (($columns -contains 'texte') -and ($columns -contains 'categorie') -and ($columns -contains 'IDcoord')) {
        Invoke-MySql @"
UPDATE $table
SET texte = CASE
    WHEN LOWER(categorie) LIKE '%mail%' OR LOWER(categorie) LIKE '%courriel%' THEN CONCAT('contact', IDcoord, '@example.invalid')
    WHEN LOWER(categorie) LIKE '%tel%' OR LOWER(categorie) LIKE '%portable%' OR LOWER(categorie) LIKE '%mobile%' THEN '0600000000'
    ELSE CONCAT('ANON_', IDcoord)
END,
intitule = CASE WHEN intitule IS NULL THEN NULL ELSE 'Coordonnee test' END;
"@ | Out-Null
        Write-Host "Anonymisé : $table" -ForegroundColor Green
    }
}

Update-IfPresent 'candidatures' ([ordered]@{
    acte_remarques     = "''"
    periodes_remarques = "''"
    poste_remarques    = "''"
    decision_remarques = "''"
})

Update-IfPresent 'adresses_mail' ([ordered]@{
    adresse      = "CONCAT('mail', IDadresse, '@example.invalid')"
    motdepasse   = "''"
    smtp         = "'localhost'"
    port         = '25'
    connexionssl = '0'
    defaut       = '0'
})

Update-IfPresent 'divers' ([ordered]@{
    motdepasse       = "''"
    save_destination = "''"
})

Update-IfPresent 'utilisateurs' ([ordered]@{
    nom    = "CONCAT('UTILISATEUR_', LPAD(IDutilisateur, 6, '0'))"
    prenom = "CONCAT('Prenom_', LPAD(IDutilisateur, 6, '0'))"
    mdp    = "''"
})

$paramCols = @(Get-Columns 'parametres')
if (($paramCols -contains 'nom') -and ($paramCols -contains 'parametre')) {
    Invoke-MySql "UPDATE parametres SET parametre='' WHERE LOWER(nom) REGEXP 'motdepasse|mot_de_passe|password|passwd|token|secret|api.?key|cle.?api';" | Out-Null
    Write-Host 'Secrets de paramètres neutralisés.' -ForegroundColor Green
}

$potential = Invoke-MySql @"
SELECT CONCAT(TABLE_NAME, '.', COLUMN_NAME)
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND LOWER(COLUMN_NAME) REGEXP 'nom|prenom|mail|courriel|adresse|telephone|tel$|portable|mobile|memo|remarque|password|passwd|motdepasse|secu|photo|commentaire|texte_libre'
ORDER BY TABLE_NAME, ORDINAL_POSITION;
"@

@(
    'Rapport d anonymisation Teamworks-CCNS'
    ('Date: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
    ''
    'Colonnes potentiellement sensibles detectees dans le schema apres traitement.'
    'Cette liste est un audit a relire : sa presence ne signifie pas que chaque colonne contient encore une donnee personnelle.'
    ''
    $potential
) | Set-Content -Encoding UTF8 $ReportFile

Write-Host "Anonymisation terminée. Audit résiduel : $ReportFile" -ForegroundColor Yellow
Write-Host 'Ne pas considérer la base comme partageable avant revue du rapport et des pièces/fichiers externes.' -ForegroundColor Yellow
