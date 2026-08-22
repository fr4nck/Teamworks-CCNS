param(
    [string]$Repo = "",
    [ValidateRange(1, 500)]
    [int]$KeepPerWorkflow = 20,
    [switch]$OnlyObsoleteWorkflows,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

function Invoke-Gh {
    param([string[]]$Arguments)

    $output = & gh @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "La commande gh a échoué : gh $($Arguments -join ' ')"
    }
    return @($output)
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) est requis pour nettoyer l'historique Actions."
}

if ([string]::IsNullOrWhiteSpace($Repo)) {
    $Repo = (Invoke-Gh @("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner") | Select-Object -First 1).Trim()
}

if ($Repo -notmatch "^[^/]+/[^/]+$") {
    throw "Dépôt invalide : '$Repo'. Format attendu : proprietaire/depot."
}

Write-Host "Dépôt : $Repo"
Write-Host "Conservation : $KeepPerWorkflow run(s) terminé(s) par workflow actif"
if ($OnlyObsoleteWorkflows) {
    Write-Host "Mode : uniquement les workflows supprimés/obsolètes"
}
if (-not $Apply) {
    Write-Host "Mode aperçu : aucune suppression ne sera effectuée."
}

$activePaths = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$workflowPaths = Invoke-Gh @(
    "api",
    "repos/$Repo/actions/workflows?per_page=100",
    "--jq",
    '.workflows[] | select(.state != "deleted") | .path'
)
foreach ($path in $workflowPaths) {
    if (-not [string]::IsNullOrWhiteSpace($path)) {
        [void]$activePaths.Add($path.Trim())
    }
}

if ($activePaths.Count -eq 0) {
    throw "Aucun workflow actif n'a été trouvé. Nettoyage annulé par sécurité."
}

Write-Host "Workflows actifs :"
$activePaths | Sort-Object | ForEach-Object { Write-Host "  - $_" }

$runLines = Invoke-Gh @(
    "api",
    "--paginate",
    "repos/$Repo/actions/runs?per_page=100",
    "--jq",
    '.workflow_runs[] | [.id, .path, .status, .created_at, .name] | @tsv'
)

$runs = foreach ($line in $runLines) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    $parts = $line -split "`t", 5
    if ($parts.Count -lt 4) {
        Write-Warning "Ligne de run ignorée car illisible : $line"
        continue
    }

    [pscustomobject]@{
        Id        = [long]$parts[0]
        Path      = $parts[1]
        Status    = $parts[2]
        CreatedAt = [datetimeoffset]$parts[3]
        Name      = if ($parts.Count -ge 5) { $parts[4] } else { "" }
    }
}

$completedRuns = @($runs | Where-Object { $_.Status -eq "completed" })
$ignoredRunning = @($runs | Where-Object { $_.Status -ne "completed" })

$candidates = [System.Collections.Generic.List[object]]::new()

foreach ($group in ($completedRuns | Group-Object Path)) {
    $path = $group.Name
    $ordered = @($group.Group | Sort-Object CreatedAt -Descending)

    if (-not $activePaths.Contains($path)) {
        foreach ($run in $ordered) {
            $candidates.Add([pscustomobject]@{
                Run    = $run
                Reason = "workflow obsolète"
            })
        }
        continue
    }

    if ($OnlyObsoleteWorkflows) {
        continue
    }

    $olderRuns = @($ordered | Select-Object -Skip $KeepPerWorkflow)
    foreach ($run in $olderRuns) {
        $candidates.Add([pscustomobject]@{
            Run    = $run
            Reason = "au-delà des $KeepPerWorkflow derniers runs"
        })
    }
}

$obsoleteCount = @($candidates | Where-Object { $_.Reason -eq "workflow obsolète" }).Count
$oldActiveCount = $candidates.Count - $obsoleteCount

Write-Host ""
Write-Host "Runs trouvés       : $($runs.Count)"
Write-Host "Runs en cours gardés: $($ignoredRunning.Count)"
Write-Host "À supprimer        : $($candidates.Count)"
Write-Host "  - anciens workflows : $obsoleteCount"
Write-Host "  - historique excédent: $oldActiveCount"

if ($candidates.Count -eq 0) {
    Write-Host "Aucun nettoyage nécessaire."
    exit 0
}

$candidates |
    Sort-Object { $_.Run.CreatedAt } -Descending |
    Select-Object @{Name="RunId";Expression={$_.Run.Id}},
                  @{Name="Date";Expression={$_.Run.CreatedAt.ToString("yyyy-MM-dd HH:mm:ss zzz")}},
                  @{Name="Workflow";Expression={$_.Run.Path}},
                  Reason |
    Format-Table -AutoSize

if (-not $Apply) {
    Write-Host ""
    Write-Host "Aperçu terminé. Relancer avec -Apply pour effectuer les suppressions."
    exit 0
}

$deleted = 0
foreach ($candidate in $candidates) {
    $run = $candidate.Run
    Write-Host "Suppression du run $($run.Id) [$($run.Path)] - $($candidate.Reason)"
    Invoke-Gh @(
        "api",
        "--method",
        "DELETE",
        "repos/$Repo/actions/runs/$($run.Id)"
    ) | Out-Null
    $deleted++
}

Write-Host ""
Write-Host "Nettoyage terminé : $deleted run(s) supprimé(s)."
