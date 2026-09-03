param(
    [string]$Repo = "",
    [ValidateRange(1, 500)]
    [int]$KeepPerWorkflow = 20,
    [ValidateRange(1, 3650)]
    [int]$DeletedBranchGraceDays = 30,
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

$defaultBranch = (Invoke-Gh @("api", "repos/$Repo", "--jq", ".default_branch") | Select-Object -First 1).Trim()
if ([string]::IsNullOrWhiteSpace($defaultBranch)) {
    throw "Branche principale introuvable. Nettoyage annulé par sécurité."
}

$liveBranches = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$branchNames = Invoke-Gh @(
    "api",
    "--paginate",
    "repos/$Repo/branches?per_page=100",
    "--jq",
    '.[].name'
)
foreach ($branch in $branchNames) {
    if (-not [string]::IsNullOrWhiteSpace($branch)) {
        [void]$liveBranches.Add($branch.Trim())
    }
}

if ($liveBranches.Count -eq 0) {
    throw "Aucune branche active n'a été trouvée. Nettoyage annulé par sécurité."
}

$activeDefaultPaths = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$workflowPaths = Invoke-Gh @(
    "api",
    "repos/$Repo/actions/workflows?per_page=100",
    "--jq",
    '.workflows[] | select(.state != "deleted") | .path'
)
foreach ($path in $workflowPaths) {
    if (-not [string]::IsNullOrWhiteSpace($path)) {
        [void]$activeDefaultPaths.Add($path.Trim())
    }
}

if ($activeDefaultPaths.Count -eq 0) {
    throw "Aucun workflow actif n'a été trouvé sur la branche principale. Nettoyage annulé par sécurité."
}

Write-Host "Dépôt : $Repo"
Write-Host "Branche principale : $defaultBranch"
Write-Host "Branches actives : $($liveBranches.Count)"
Write-Host "Conservation : $KeepPerWorkflow run(s) terminé(s) par couple branche + workflow"
Write-Host "Délai de sécurité pour branche absente : $DeletedBranchGraceDays jour(s)"
if ($OnlyObsoleteWorkflows) {
    Write-Host "Mode : uniquement les workflows obsolètes et branches absentes hors délai de sécurité"
}
if (-not $Apply) {
    Write-Host "Mode aperçu : aucune suppression ne sera effectuée."
}

$runLines = Invoke-Gh @(
    "api",
    "--paginate",
    "repos/$Repo/actions/runs?per_page=100",
    "--jq",
    '.workflow_runs[] | [.id, .path, .status, .created_at, (.head_branch // "__NO_BRANCH__"), .name] | @tsv'
)

$runs = foreach ($line in $runLines) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    $parts = $line -split "`t", 6
    if ($parts.Count -lt 5) {
        Write-Warning "Ligne de run ignorée car illisible : $line"
        continue
    }

    $branch = if ($parts[4] -eq "__NO_BRANCH__") { "" } else { $parts[4] }
    [pscustomobject]@{
        Id        = [long]$parts[0]
        Path      = $parts[1]
        Status    = $parts[2]
        CreatedAt = [datetimeoffset]$parts[3]
        Branch    = $branch
        Name      = if ($parts.Count -ge 6) { $parts[5] } else { "" }
    }
}

$completedRuns = @($runs | Where-Object { $_.Status -eq "completed" } | Sort-Object CreatedAt -Descending)
$ignoredRunning = @($runs | Where-Object { $_.Status -ne "completed" })
$graceCutoff = [datetimeoffset]::UtcNow.AddDays(-$DeletedBranchGraceDays)
$seenByBranchWorkflow = @{}
$candidates = [System.Collections.Generic.List[object]]::new()
$graceProtected = 0

foreach ($run in $completedRuns) {
    $branchExists = -not [string]::IsNullOrWhiteSpace($run.Branch) -and $liveBranches.Contains($run.Branch)

    if ($branchExists) {
        if ($run.Branch -eq $defaultBranch -and -not $activeDefaultPaths.Contains($run.Path)) {
            $candidates.Add([pscustomobject]@{
                Run    = $run
                Reason = "workflow obsolète sur la branche principale"
            })
            continue
        }

        if ($OnlyObsoleteWorkflows) {
            continue
        }

        $key = $run.Branch + "`t" + $run.Path
        $count = if ($seenByBranchWorkflow.ContainsKey($key)) { [int]$seenByBranchWorkflow[$key] } else { 0 }
        if ($count -lt $KeepPerWorkflow) {
            $seenByBranchWorkflow[$key] = $count + 1
        } else {
            $candidates.Add([pscustomobject]@{
                Run    = $run
                Reason = "au-delà des $KeepPerWorkflow derniers runs de cette branche et de ce workflow"
            })
        }
        continue
    }

    if ($run.CreatedAt -le $graceCutoff) {
        $candidates.Add([pscustomobject]@{
            Run    = $run
            Reason = "branche absente et run âgé d'au moins $DeletedBranchGraceDays jours"
        })
    } else {
        $graceProtected++
    }
}

$obsoleteCount = @($candidates | Where-Object { $_.Reason -like "workflow obsolète*" }).Count
$deletedBranchCount = @($candidates | Where-Object { $_.Reason -like "branche absente*" }).Count
$trimCount = $candidates.Count - $obsoleteCount - $deletedBranchCount

Write-Host ""
Write-Host "Runs trouvés               : $($runs.Count)"
Write-Host "Runs en cours gardés        : $($ignoredRunning.Count)"
Write-Host "Branches absentes protégées : $graceProtected run(s)"
Write-Host "À supprimer                 : $($candidates.Count)"
Write-Host "  - workflows obsolètes     : $obsoleteCount"
Write-Host "  - branches absentes       : $deletedBranchCount"
Write-Host "  - historique excédentaire : $trimCount"

if ($candidates.Count -eq 0) {
    Write-Host "Aucun nettoyage nécessaire."
    exit 0
}

$candidates |
    Sort-Object { $_.Run.CreatedAt } -Descending |
    Select-Object @{Name="RunId";Expression={$_.Run.Id}},
                  @{Name="Date";Expression={$_.Run.CreatedAt.ToString("yyyy-MM-dd HH:mm:ss zzz")}},
                  @{Name="Branche";Expression={$_.Run.Branch}},
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
    Write-Host "Suppression du run $($run.Id) [$($run.Branch) / $($run.Path)] - $($candidate.Reason)"
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
