[CmdletBinding()]
param(
    [ValidateSet("uia", "win32")]
    [string]$Backend = "uia",

    [ValidateRange(5, 300)]
    [int]$Timeout = 30
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$RepoRoot = (Resolve-Path $PSScriptRoot).Path
$InnerLauncher = Join-Path $RepoRoot "tools\recette_windows\run_local.ps1"
$ArtifactsRoot = Join-Path $RepoRoot "artifacts\recette-windows"
$Scenario = "individus-smoke"
$BlockedExitCodes = @(4, 10, 11, 12, 13, 14)

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )
    $Value | ConvertTo-Json -Depth 10 | Set-Content -Path $Path -Encoding UTF8
}

function New-FallbackArtifactDirectory {
    New-Item -ItemType Directory -Force $ArtifactsRoot | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $path = Join-Path $ArtifactsRoot ("local-{0}-{1}" -f $stamp, $Scenario)
    New-Item -ItemType Directory -Force $path | Out-Null
    return $path
}

function Find-ArtifactDirectory {
    param([object[]]$OutputLines)

    $found = $null
    foreach ($entry in $OutputLines) {
        $line = "$entry"
        if ($line -match '^(?:Résultats|Resultats)\s*:\s*(.+)$') {
            $candidate = $Matches[1].Trim()
            if ($candidate) {
                $found = $candidate
            }
        }
    }
    if ($found -and (Test-Path -LiteralPath $found -PathType Container)) {
        return (Resolve-Path -LiteralPath $found).Path
    }

    if (Test-Path -LiteralPath $ArtifactsRoot -PathType Container) {
        $latest = Get-ChildItem -LiteralPath $ArtifactsRoot -Directory -Filter "local-*-individus-smoke" |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($latest) {
            return $latest.FullName
        }
    }
    return (New-FallbackArtifactDirectory)
}

function Update-ResultStatus {
    param(
        [Parameter(Mandatory = $true)][string]$ArtifactDir,
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$Verdict,
        [Parameter(Mandatory = $true)][int]$InnerExitCode,
        [Parameter(Mandatory = $true)][object[]]$InnerOutput
    )

    $outputPath = Join-Path $ArtifactDir "launcher-output.log"
    @($InnerOutput | ForEach-Object { "$_" }) | Set-Content -Path $outputPath -Encoding UTF8

    $resultPath = Join-Path $ArtifactDir "result.json"
    if (Test-Path -LiteralPath $resultPath -PathType Leaf) {
        try {
            $result = Get-Content -Raw -LiteralPath $resultPath | ConvertFrom-Json
            if ($Status -eq "BLOCKED") {
                $result.status = "BLOCKED"
            }
            $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resultPath -Encoding UTF8
        }
        catch {
            Set-Content -Path (Join-Path $ArtifactDir "result-normalization-error.txt") -Value $_.Exception.ToString() -Encoding UTF8
        }
    }
    elseif ($Status -eq "BLOCKED") {
        Write-JsonFile -Path $resultPath -Value ([ordered]@{
            scenario = $Scenario
            status = "BLOCKED"
            backend = $Backend
            exit_status = $InnerExitCode
            error = "Précondition locale non satisfaite; voir launcher-output.log."
        })
    }

    Write-JsonFile -Path (Join-Path $ArtifactDir "launcher-result.json") -Value ([ordered]@{
        scenario = $Scenario
        status = $Status
        verdict = $Verdict
        backend = $Backend
        timeout = $Timeout
        inner_exit_code = $InnerExitCode
        artifacts = $ArtifactDir
        completed_at = (Get-Date).ToString("o")
    })
}

$InnerOutput = @()
$InnerExitCode = 4

if (-not (Test-Path -LiteralPath $InnerLauncher -PathType Leaf)) {
    $InnerOutput = @("Lanceur interne introuvable : $InnerLauncher")
}
else {
    $shellName = if ($PSVersionTable.PSEdition -eq "Core") { "pwsh.exe" } else { "powershell.exe" }
    $ChildShell = Join-Path $PSHOME $shellName
    if (-not (Test-Path -LiteralPath $ChildShell -PathType Leaf)) {
        $command = Get-Command $shellName -ErrorAction SilentlyContinue
        if ($command) {
            $ChildShell = $command.Source
        }
    }

    if (-not (Test-Path -LiteralPath $ChildShell -PathType Leaf)) {
        $InnerOutput = @("Sous-processus PowerShell introuvable : $shellName")
    }
    else {
        $previousNativePreference = $null
        if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
            $previousNativePreference = $PSNativeCommandUseErrorActionPreference
            $PSNativeCommandUseErrorActionPreference = $false
        }
        try {
            $InnerOutput = @(& $ChildShell -NoProfile -ExecutionPolicy Bypass -File $InnerLauncher -Backend $Backend -Timeout $Timeout 2>&1)
            $InnerExitCode = $LASTEXITCODE
        }
        catch {
            $InnerOutput = @($_.Exception.ToString())
            $InnerExitCode = 4
        }
        finally {
            if ($null -ne $previousNativePreference) {
                $PSNativeCommandUseErrorActionPreference = $previousNativePreference
            }
        }
    }
}

$ArtifactDir = Find-ArtifactDirectory -OutputLines $InnerOutput

if ($InnerExitCode -eq 0) {
    $Status = "PASS"
    $Verdict = "RECETTE OK"
    $ExitCode = 0
}
elseif ($BlockedExitCodes -contains $InnerExitCode) {
    $Status = "BLOCKED"
    $Verdict = "ENVIRONNEMENT NON QUALIFIABLE"
    $ExitCode = 4
}
else {
    $Status = "FAIL"
    $Verdict = "RECETTE KO"
    $ExitCode = $InnerExitCode
    if ($ExitCode -eq 0) {
        $ExitCode = 2
    }
}

Update-ResultStatus -ArtifactDir $ArtifactDir -Status $Status -Verdict $Verdict -InnerExitCode $InnerExitCode -InnerOutput $InnerOutput

Write-Host $Verdict
Write-Host ("RESULTATS: {0}" -f $ArtifactDir)
exit $ExitCode
