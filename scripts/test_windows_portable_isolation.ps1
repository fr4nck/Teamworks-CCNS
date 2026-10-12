[CmdletBinding()]
param(
    [string]$ExpectedCommit = $env:GITHUB_SHA,
    [string]$PackageDirectory = "",
    [ValidateRange(10, 180)][int]$StartupTimeoutSeconds = 45
)

$ErrorActionPreference = 'Stop'

# Conserver l'ancien point d'entree, avec une seule qualification maintenue.
# Le rapport et la copie restent dans un dossier temporaire unique, dont le
# chemin est affiche par le harnais, sans nettoyer ni renommer le checkout.
$qualificationScript = Join-Path $PSScriptRoot 'test_windows_portable_isolated.ps1'
& $qualificationScript @PSBoundParameters
