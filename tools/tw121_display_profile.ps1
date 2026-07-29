param(
    [Parameter(Mandatory = $true)]
    [string]$Config,

    [ValidateSet("Systeme", "Système", "Clair", "Sombre")]
    [string]$Theme = "Systeme",

    [ValidateRange(80, 200)]
    [int]$Scale = 100,

    [switch]$CheckOnly,

    [string]$Restore,

    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Tool = Join-Path $ScriptDir "tw121_display_profile.py"

if (-not (Test-Path -LiteralPath $Tool -PathType Leaf)) {
    Write-Error "Outil introuvable : $Tool"
    exit 2
}

$Arguments = @($Tool, $Config)

if ($Restore) {
    if ($CheckOnly) {
        Write-Error "-Restore ne peut pas être combiné avec -CheckOnly."
        exit 2
    }
    $Arguments += @("--restore", $Restore)
} else {
    $Arguments += @("--theme", $Theme, "--scale", $Scale)
    if ($CheckOnly) {
        $Arguments += "--check-only"
    }
}

Write-Host "TW-122 - Profil d'affichage Windows"
Write-Host "Configuration : $Config"

& $Python @Arguments
$ExitCode = $LASTEXITCODE

if ($ExitCode -ne 0) {
    Write-Error "Validation TW-122 en échec (code $ExitCode)."
    exit $ExitCode
}

if ($Restore) {
    Write-Host "Configuration restaurée. Relancez Teamworks-CCNS."
} elseif ($CheckOnly) {
    Write-Host "Configuration vérifiée sans modification."
} else {
    Write-Host "Profil appliqué. Fermez puis relancez Teamworks-CCNS."
}

exit 0
