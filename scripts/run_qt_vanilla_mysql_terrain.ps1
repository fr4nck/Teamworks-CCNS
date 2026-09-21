param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Start", "Finish", "Performance")]
    [string]$Action,

    [Parameter(Mandatory = $true)]
    [string]$Database,

    [Parameter(Mandatory = $true)]
    [string]$Sha,

    [string]$HostName = "127.0.0.1",
    [int]$Port = 3306,
    [string]$User = "root",
    [string]$EvidenceDir = ".\preuves-qt-vanilla-0.1",
    [string]$PortableArtifact,
    [string]$SetupArtifact,
    [string]$PerformanceCsv
)

$ErrorActionPreference = "Stop"

function Assert-SafeDatabaseName {
    param([string]$Name)
    if (-not $Name.EndsWith("_qt_vanilla_recette")) {
        throw "Base refusée : le nom doit se terminer par '_qt_vanilla_recette'."
    }
    if ($Name -notmatch '^[A-Za-z0-9_]+$') {
        throw "Base refusée : nom MySQL invalide."
    }
}

function Assert-Sha {
    param([string]$Value)
    if ($Value -notmatch '^[0-9a-fA-F]{40}$') {
        throw "SHA refusé : 40 caractères hexadécimaux attendus."
    }
}

function Resolve-ExistingFile {
    param([string]$PathValue, [string]$Label)
    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return $null
    }
    $resolved = Resolve-Path -LiteralPath $PathValue -ErrorAction Stop
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "$Label introuvable : $PathValue"
    }
    return $resolved.Path
}

function Set-MySqlPasswordEnvironment {
    if (-not [string]::IsNullOrEmpty($env:TEAMWORKS_MYSQL_PASSWORD)) {
        return
    }

    $secure = Read-Host "Mot de passe MySQL du compte de recette" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        $env:TEAMWORKS_MYSQL_PASSWORD = $plain
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

function Invoke-Collector {
    param([string[]]$Arguments)

    & python "tools/collect_qt_vanilla_mysql_evidence.py" @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Le collecteur de preuves a échoué (code $LASTEXITCODE)."
    }
}

Assert-SafeDatabaseName $Database
Assert-Sha $Sha

$EvidenceDir = [System.IO.Path]::GetFullPath($EvidenceDir)
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

$env:TEAMWORKS_MYSQL_HOST = $HostName
$env:TEAMWORKS_MYSQL_PORT = [string]$Port
$env:TEAMWORKS_MYSQL_USER = $User

try {
    if ($Action -eq "Start") {
        Set-MySqlPasswordEnvironment

        $portable = Resolve-ExistingFile $PortableArtifact "ZIP portable"
        $setup = Resolve-ExistingFile $SetupArtifact "Setup Windows"

        $args = @(
            "snapshot",
            "--database", $Database,
            "--sha", $Sha,
            "--label", "before",
            "--output", (Join-Path $EvidenceDir "mysql-before.json")
        )
        if ($portable) {
            $args += @("--artifact", $portable)
        }
        if ($setup) {
            $args += @("--artifact", $setup)
        }

        Invoke-Collector $args

        $pvTemplate = "docs\PV_RECETTE_QT_VANILLA_0.1_MYSQL.md"
        $pvTarget = Join-Path $EvidenceDir "PV_RECETTE_QT_VANILLA_0.1_MYSQL-rempli.md"
        if ((Test-Path -LiteralPath $pvTemplate) -and -not (Test-Path -LiteralPath $pvTarget)) {
            Copy-Item -LiteralPath $pvTemplate -Destination $pvTarget
        }

        Write-Host ""
        Write-Host "=== RECETTE TERRAIN PRETE ==="
        Write-Host "SHA       : $Sha"
        Write-Host "Base      : $Database"
        Write-Host "Preuves   : $EvidenceDir"
        Write-Host ""
        Write-Host "Dérouler maintenant :"
        Write-Host "  docs\MATRICE_VALIDATION_QT_VANILLA_0.1_MYSQL.md"
        Write-Host "  docs\SEUILS_PERFORMANCE_QT_VANILLA_0.1.md"
        Write-Host "  $pvTarget"
        Write-Host ""
        Write-Host "Quand la recette fonctionnelle est terminée, relancer avec -Action Finish."
    }
    elseif ($Action -eq "Finish") {
        Set-MySqlPasswordEnvironment

        $before = Join-Path $EvidenceDir "mysql-before.json"
        if (-not (Test-Path -LiteralPath $before)) {
            throw "Snapshot avant absent : $before. Exécuter d'abord -Action Start."
        }

        $portable = Resolve-ExistingFile $PortableArtifact "ZIP portable"
        $setup = Resolve-ExistingFile $SetupArtifact "Setup Windows"

        $args = @(
            "snapshot",
            "--database", $Database,
            "--sha", $Sha,
            "--label", "after",
            "--output", (Join-Path $EvidenceDir "mysql-after.json")
        )
        if ($portable) {
            $args += @("--artifact", $portable)
        }
        if ($setup) {
            $args += @("--artifact", $setup)
        }

        Invoke-Collector $args

        Invoke-Collector @(
            "compare",
            "--before", $before,
            "--after", (Join-Path $EvidenceDir "mysql-after.json"),
            "--output", (Join-Path $EvidenceDir "mysql-compare.json")
        )

        Write-Host ""
        Write-Host "=== COMPARAISON TERMINEE ==="
        Write-Host "Lire : $(Join-Path $EvidenceDir 'mysql-compare.json')"
        Write-Host "Les deltas de comptage doivent être expliqués dans le PV."
    }
    elseif ($Action -eq "Performance") {
        if ([string]::IsNullOrWhiteSpace($PerformanceCsv)) {
            throw "-PerformanceCsv est obligatoire avec -Action Performance."
        }
        $csv = Resolve-ExistingFile $PerformanceCsv "CSV de performance"

        Invoke-Collector @(
            "performance",
            "--input", $csv,
            "--output", (Join-Path $EvidenceDir "performance-summary.json")
        )

        Write-Host ""
        Write-Host "=== PERFORMANCE CALCULEE ==="
        Write-Host "Lire : $(Join-Path $EvidenceDir 'performance-summary.json')"
    }
}
finally {
    Remove-Item Env:TEAMWORKS_MYSQL_PASSWORD -ErrorAction SilentlyContinue
}
