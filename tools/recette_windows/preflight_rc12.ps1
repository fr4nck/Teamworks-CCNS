[CmdletBinding()]
param(
    [string]$Portable = 'C:\_Atelier_IA\Teamworks-CCNS\Recette-RC12\run-42675793471\Portable',
    [string]$Rapports = 'C:\_Atelier_IA\Teamworks-CCNS\Stabilisation-wx-0.9.2'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

# Lecture des fichiers du paquet seulement.
# Aucun lancement de Teamworks, aucun acces SQL, aucun envoi de courriel,
# aucune suppression, aucun changement de configuration ni installation.

$CommitAttendu = '9b02fbe94016b403255eabdaa856176d7f3e0ac5'
$VersionAttendue = '0.9.2-rc12'
$RapportsAutorises = 'C:\_Atelier_IA\Teamworks-CCNS\'
$CompteAttendu = 2278

$Etat = 'NON TESTE'
$Motif = ''
$NombreFichiers = 0
$RapportFichier = $null

Write-Host '=== TEAMWORKS WX 0.9.2 / PREFLIGHT RC12 ===' -ForegroundColor Cyan
Write-Host 'Lecture seule du paquet. Aucun acces a la base ni envoi email.'

try {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw 'Ce precontrole est destine a Windows.'
    }

    $RapportsComplet = [System.IO.Path]::GetFullPath($Rapports).TrimEnd('\') + '\'
    if (-not $RapportsComplet.StartsWith(
        $RapportsAutorises,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw 'Repertoire de rapport non autorise : utiliser C:\_Atelier_IA\Teamworks-CCNS\...'
    }

    $PortableComplet = [System.IO.Path]::GetFullPath($Portable).TrimEnd('\') + '\'
    foreach ($Nom in @('Teamworks-CCNS.exe', 'BUILD.txt', 'VERSION', 'PACKAGE-SHA256SUMS.txt')) {
        $Chemin = Join-Path $PortableComplet $Nom
        if (-not (Test-Path -LiteralPath $Chemin -PathType Leaf)) {
            throw "Element du portable absent : $Nom"
        }
    }

    $Version = (Get-Content -LiteralPath (Join-Path $PortableComplet 'VERSION') -Raw).Trim()
    $Build = Get-Content -LiteralPath (Join-Path $PortableComplet 'BUILD.txt') -Raw

    if ($Version -ne $VersionAttendue) { throw "Version inattendue : $Version" }
    if (-not $Build.Contains($CommitAttendu)) { throw 'Commit du paquet non conforme.' }
    Write-Host 'PASS : version et commit du paquet' -ForegroundColor Green

    $Manifest = Join-Path $PortableComplet 'PACKAGE-SHA256SUMS.txt'
    $Lignes = @(Get-Content -LiteralPath $Manifest -Encoding UTF8 |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) })

    if ($Lignes.Count -ne $CompteAttendu) {
        throw "Nombre de lignes du manifeste inattendu : $($Lignes.Count)"
    }

    $Vus = @{}
    foreach ($Ligne in $Lignes) {
        if ($Ligne -notmatch '^([0-9a-fA-F]{64})  (.+)$') {
            throw 'Format du manifeste invalide.'
        }

        $HashAttendu = $Matches[1].ToLowerInvariant()
        $Relatif = $Matches[2]

        if ($Relatif -match '(^[\\/]|^[A-Za-z]:|(^|[\\/])\.\.([\\/]|$))') {
            throw 'Chemin suspect dans le manifeste.'
        }

        $Cle = $Relatif.Replace('\\', '/').ToLowerInvariant()
        if ($Vus.ContainsKey($Cle)) { throw "Entree dupliquee : $Relatif" }
        $Vus[$Cle] = $true

        $Fichier = [System.IO.Path]::GetFullPath(
            (Join-Path $PortableComplet ($Relatif.Replace('/', '\')))
        )
        if (-not $Fichier.StartsWith(
            $PortableComplet,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            throw 'Chemin sortant du dossier portable.'
        }
        if (-not (Test-Path -LiteralPath $Fichier -PathType Leaf)) {
            throw "Fichier absent : $Relatif"
        }

        $Reel = (Get-FileHash -LiteralPath $Fichier -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($Reel -ne $HashAttendu) {
            throw "Somme SHA256 differente : $Relatif"
        }
        $NombreFichiers++
    }

    $Etat = 'PASS'
    Write-Host "PASS : $NombreFichiers fichiers verifies (SHA256)" -ForegroundColor Green
}
catch {
    $Etat = 'ECHEC'
    $Motif = $_.Exception.Message
    Write-Host "ECHEC : $Motif" -ForegroundColor Red
}
finally {
    # Les rapports ne contiennent aucun contenu de fichier, identifiant,
    # configuration RH, capture d'ecran ou secret.
    try {
        $RapportsComplet = [System.IO.Path]::GetFullPath($Rapports).TrimEnd('\') + '\'
        if ($RapportsComplet.StartsWith(
            $RapportsAutorises,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            New-Item -ItemType Directory -Path $RapportsComplet -Force | Out-Null
            $FichierNom = 'preflight-rc12-' + (Get-Date -Format 'yyyyMMdd-HHmmss') +
                '-' + ([guid]::NewGuid().ToString('N').Substring(0, 8)) + '.json'
            $RapportFichier = Join-Path $RapportsComplet $FichierNom
            $Synthese = [ordered]@{
                date = (Get-Date).ToString('o')
                controle = 'preflight portable RC12 en lecture seule'
                version_attendue = $VersionAttendue
                commit_attendu = $CommitAttendu
                statut = $Etat
                fichiers_verifies = $NombreFichiers
                motif_echec = $Motif
                recette_metier = 'NON TESTEE'
                base_de_recette_independante = 'NON VERIFIEE'
                decision_version_stable = 'NON AUTORISEE'
            }
            $Synthese | ConvertTo-Json -Depth 4 |
                Set-Content -LiteralPath $RapportFichier -Encoding UTF8 -NoNewline
            Write-Host "Rapport local : $RapportFichier"
        }
    }
    catch {
        Write-Warning "Impossible d'ecrire le rapport : $($_.Exception.Message)"
    }
}

if ($Etat -ne 'PASS') {
    throw "Preflight RC12 non valide : $Motif"
}

Write-Host 'PREVOL OK / RECETTE METIER ENCORE A FAIRE' -ForegroundColor Yellow
Write-Host 'Aucun logiciel installe ni lance ; aucune base modifiee.'
