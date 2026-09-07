[CmdletBinding()]
param(
    [ValidateSet("uia", "win32")]
    [string]$Backend = "uia",

    [ValidateRange(5, 300)]
    [int]$Timeout = 30
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$Scenario = "individus-smoke"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ArtifactsRoot = Join-Path $RepoRoot "artifacts\recette-windows"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ArtifactDir = Join-Path $ArtifactsRoot ("local-{0}-{1}" -f $Stamp, $Scenario)
$ZipPath = "$ArtifactDir.zip"

New-Item -ItemType Directory -Force $ArtifactDir | Out-Null
Set-Location $RepoRoot

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        $Value
    )

    $json = $Value | ConvertTo-Json -Depth 8
    Set-Content -Path $Path -Value $json -Encoding UTF8
}

function Ensure-ResultFile {
    param(
        [string]$Status,
        [int]$ExitCode,
        [string]$Reason
    )

    $resultPath = Join-Path $ArtifactDir "result.json"
    if (-not (Test-Path $resultPath)) {
        Write-JsonFile -Path $resultPath -Value ([ordered]@{
            scenario = $Scenario
            status = $Status
            exit_status = $ExitCode
            reason = $Reason
            backend = $Backend
        })
    }
}

function Complete-LocalRun {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("ok", "ko", "environment")]
        [string]$Kind,
        [Parameter(Mandatory = $true)]
        [int]$ExitCode,
        [string]$Reason = ""
    )

    $verdict = switch ($Kind) {
        "ok" { "RECETTE OK" }
        "ko" { "RECETTE KO" }
        default { "ENVIRONNEMENT NON PRÊT" }
    }

    Ensure-ResultFile -Status $Kind -ExitCode $ExitCode -Reason $Reason
    Write-JsonFile -Path (Join-Path $ArtifactDir "local-run.json") -Value ([ordered]@{
        verdict = $verdict
        reason = $Reason
        exit_code = $ExitCode
        scenario = $Scenario
        backend = $Backend
        artifacts = $ArtifactDir
        zip = $ZipPath
        completed_at = (Get-Date).ToString("o")
    })

    try {
        if (Test-Path $ZipPath) {
            Remove-Item -Force $ZipPath
        }
        Compress-Archive -Path (Join-Path $ArtifactDir "*") -DestinationPath $ZipPath -Force
    }
    catch {
        $zipError = "Impossible de créer le ZIP : $($_.Exception.Message)"
        Set-Content -Path (Join-Path $ArtifactDir "zip-error.txt") -Value $zipError -Encoding UTF8
        if ($Kind -eq "ok") {
            $Kind = "ko"
            $ExitCode = 2
            $verdict = "RECETTE KO"
            $Reason = $zipError
        }
    }

    Write-Host ""
    if ($Reason) {
        Write-Host ("{0} — {1}" -f $verdict, $Reason)
    }
    elseif ($Kind -eq "ko") {
        Write-Host ("{0} — voir {1}" -f $verdict, $ArtifactDir)
    }
    else {
        Write-Host $verdict
    }
    Write-Host ("Résultats : {0}" -f $ArtifactDir)
    if (Test-Path $ZipPath) {
        Write-Host ("ZIP       : {0}" -f $ZipPath)
    }
    exit $ExitCode
}

function Get-Python311 {
    $candidates = @()

    $py = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($py) {
        $candidates += [pscustomobject]@{ Exe = $py.Source; Prefix = @("-3.11") }
    }

    foreach ($name in @("python.exe", "python3.11.exe")) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) {
            $candidates += [pscustomobject]@{ Exe = $command.Source; Prefix = @() }
        }
    }

    foreach ($candidate in $candidates) {
        $versionArgs = @($candidate.Prefix) + @(
            "-c",
            "import sys; print('.'.join(str(x) for x in sys.version_info[:3]))"
        )
        $version = & $candidate.Exe @versionArgs 2>$null
        if ($LASTEXITCODE -eq 0 -and "$version" -match '^3\.11\.') {
            return [pscustomobject]@{
                Exe = $candidate.Exe
                Prefix = @($candidate.Prefix)
                Version = "$version".Trim()
            }
        }
    }
    return $null
}

$isWindows = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
if (-not $isWindows) {
    Complete-LocalRun -Kind "environment" -ExitCode 10 -Reason "Ce lanceur doit être exécuté sous Windows."
}

if (-not ("TeamworksRecipeNative" -as [type])) {
    try {
        Add-Type -TypeDefinition @'
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

public static class TeamworksRecipeNative {
    [DllImport("user32.dll", SetLastError=true)]
    private static extern IntPtr OpenInputDesktop(uint flags, bool inherit, uint desiredAccess);

    [DllImport("user32.dll", SetLastError=true)]
    private static extern bool CloseDesktop(IntPtr desktop);

    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    private static extern bool GetUserObjectInformation(
        IntPtr handle, int index, StringBuilder info, uint length, out uint needed);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern uint GetDpiForSystem();

    [DllImport("user32.dll")]
    public static extern int GetSystemMetrics(int index);

    [DllImport("shcore.dll")]
    private static extern int GetProcessDpiAwareness(IntPtr process, out int awareness);

    public static int GetCurrentProcessDpiAwareness() {
        int awareness;
        int result = GetProcessDpiAwareness(Process.GetCurrentProcess().Handle, out awareness);
        return result == 0 ? awareness : -1;
    }

    public static string GetInputDesktopName() {
        const uint DESKTOP_READOBJECTS = 0x0001;
        const int UOI_NAME = 2;
        IntPtr desktop = OpenInputDesktop(0, false, DESKTOP_READOBJECTS);
        if (desktop == IntPtr.Zero) return null;
        try {
            var buffer = new StringBuilder(256);
            uint needed;
            if (!GetUserObjectInformation(desktop, UOI_NAME, buffer, 512, out needed)) return null;
            return buffer.ToString();
        }
        finally {
            CloseDesktop(desktop);
        }
    }
}
'@
    }
    catch {
        Complete-LocalRun -Kind "environment" -ExitCode 10 -Reason ("API Windows indisponible : {0}" -f $_.Exception.Message)
    }
}

$SessionName = [Environment]::GetEnvironmentVariable("SESSIONNAME")
$SessionId = (Get-Process -Id $PID).SessionId
$UserInteractive = [Environment]::UserInteractive
$InputDesktop = [TeamworksRecipeNative]::GetInputDesktopName()
$ForegroundHwnd = [TeamworksRecipeNative]::GetForegroundWindow().ToInt64()

if (-not $UserInteractive) {
    Complete-LocalRun -Kind "environment" -ExitCode 10 -Reason "Windows indique que le processus n'est pas interactif."
}
if ($SessionId -le 0) {
    Complete-LocalRun -Kind "environment" -ExitCode 10 -Reason ("Session Windows non utilisateur (SessionId={0})." -f $SessionId)
}
if (-not $SessionName -or $SessionName.Trim().ToLowerInvariant() -eq "services") {
    Complete-LocalRun -Kind "environment" -ExitCode 10 -Reason ("SESSIONNAME n'identifie pas une session utilisateur interactive : '{0}'." -f $SessionName)
}
if ($InputDesktop -ne "Default") {
    Complete-LocalRun -Kind "environment" -ExitCode 10 -Reason ("Le bureau d'entrée n'est pas le bureau utilisateur déverrouillé 'Default' : '{0}'." -f $InputDesktop)
}
if ($ForegroundHwnd -eq 0) {
    Complete-LocalRun -Kind "environment" -ExitCode 10 -Reason "Aucune fenêtre de premier plan Windows n'est accessible."
}

$Python = Get-Python311
if ($null -eq $Python) {
    Complete-LocalRun -Kind "environment" -ExitCode 11 -Reason "Python 3.11 est introuvable (py -3.11 / python.exe)."
}

$Launcher = Join-Path $RepoRoot "run_teamworks.py"
$RecipeRequirements = Join-Path $RepoRoot "requirements\recette-windows.txt"
if (-not (Test-Path $Launcher -PathType Leaf)) {
    Complete-LocalRun -Kind "environment" -ExitCode 12 -Reason ("Lanceur Teamworks introuvable : {0}" -f $Launcher)
}
if (-not (Test-Path $RecipeRequirements -PathType Leaf)) {
    Complete-LocalRun -Kind "environment" -ExitCode 12 -Reason ("Dépendances de recette introuvables : {0}" -f $RecipeRequirements)
}

$TeamworksCheckArgs = @($Python.Prefix) + @(
    "-c",
    "from pathlib import Path; import wx; p=Path('run_teamworks.py'); compile(p.read_text(encoding='utf-8'), str(p), 'exec'); print(wx.version())"
)
$TeamworksCheck = & $Python.Exe @TeamworksCheckArgs 2>&1
$TeamworksCheckCode = $LASTEXITCODE
$TeamworksCheck | Set-Content -Path (Join-Path $ArtifactDir "teamworks-environment-check.txt") -Encoding UTF8
if ($TeamworksCheckCode -ne 0) {
    Complete-LocalRun -Kind "environment" -ExitCode 13 -Reason "L'environnement Python Teamworks/wx n'est pas prêt ; voir teamworks-environment-check.txt."
}

$Dpi = $null
$ScalePercent = $null
$DpiAwareness = $null
try {
    $detectedAwareness = [TeamworksRecipeNative]::GetCurrentProcessDpiAwareness()
    if ($detectedAwareness -ge 0) {
        $DpiAwareness = [int]$detectedAwareness
    }
    # GetDpiForSystem renvoie 96 par virtualisation pour un processus DPI-unaware.
    # On ne publie donc un scaling que si le processus est réellement DPI-aware.
    if ($DpiAwareness -in @(1, 2)) {
        $detectedDpi = [TeamworksRecipeNative]::GetDpiForSystem()
        if ($detectedDpi -gt 0) {
            $Dpi = [int]$detectedDpi
            $ScalePercent = [int][Math]::Round(($Dpi / 96.0) * 100.0)
        }
    }
}
catch {
    # Les valeurs restent null : aucun pourcentage n'est inventé.
}

$WindowsCaption = $null
try {
    $WindowsCaption = (Get-CimInstance Win32_OperatingSystem -ErrorAction Stop).Caption
}
catch {
    $WindowsCaption = $null
}

$EnvironmentInfo = [ordered]@{
    captured_at = (Get-Date).ToString("o")
    repository_root = $RepoRoot
    scenario = $Scenario
    backend = $Backend
    windows = [ordered]@{
        caption = $WindowsCaption
        version = [Environment]::OSVersion.Version.ToString()
        is_64_bit_os = [Environment]::Is64BitOperatingSystem
        user_interactive = $UserInteractive
        session_name = $SessionName
        session_id = $SessionId
        input_desktop = $InputDesktop
        foreground_hwnd = $ForegroundHwnd
    }
    python = [ordered]@{
        executable = $Python.Exe
        prefix = @($Python.Prefix)
        version = $Python.Version
    }
    display = [ordered]@{
        width_px = [TeamworksRecipeNative]::GetSystemMetrics(0)
        height_px = [TeamworksRecipeNative]::GetSystemMetrics(1)
        process_dpi_awareness = $DpiAwareness
        system_dpi = $Dpi
        system_scaling_percent = $ScalePercent
        scaling_source = $(if ($null -ne $Dpi) { "GetDpiForSystem from a DPI-aware process" } else { $null })
        scope = $(if ($null -ne $Dpi) { "system DPI; not claimed as per-monitor DPI" } else { "not reliably detected" })
    }
    powershell = $PSVersionTable.PSVersion.ToString()
}
Write-JsonFile -Path (Join-Path $ArtifactDir "environment.json") -Value $EnvironmentInfo

$PipStdout = Join-Path $ArtifactDir "pip-stdout.log"
$PipStderr = Join-Path $ArtifactDir "pip-stderr.log"
$PipArgs = @($Python.Prefix) + @(
    "-m", "pip", "install", "--disable-pip-version-check",
    "--requirement", $RecipeRequirements
)
& $Python.Exe @PipArgs 1> $PipStdout 2> $PipStderr
$PipExitCode = $LASTEXITCODE
if ($PipExitCode -ne 0) {
    Complete-LocalRun -Kind "environment" -ExitCode 14 -Reason "Installation de requirements\recette-windows.txt impossible ; voir pip-stderr.log."
}

$RecipeStdout = Join-Path $ArtifactDir "runner-stdout.log"
$RecipeStderr = Join-Path $ArtifactDir "runner-stderr.log"
$RecipeArgs = @($Python.Prefix) + @(
    "-m", "tools.recette_windows",
    "--scenario", $Scenario,
    "--backend", $Backend,
    "--timeout", "$Timeout",
    "--artifacts", $ArtifactDir
)

& $Python.Exe @RecipeArgs 1> $RecipeStdout 2> $RecipeStderr
$RecipeExitCode = $LASTEXITCODE

if ($RecipeExitCode -eq 0) {
    Complete-LocalRun -Kind "ok" -ExitCode 0
}

$RecipeReason = ""
if (Test-Path $RecipeStderr) {
    $lastErrorLine = Get-Content $RecipeStderr | Where-Object { $_.Trim() } | Select-Object -Last 1
    if ($lastErrorLine) {
        $RecipeReason = "$lastErrorLine".Trim()
    }
}

if ($RecipeExitCode -eq 4) {
    if (-not $RecipeReason) { $RecipeReason = "Le pilote a refusé l'environnement Windows." }
    Complete-LocalRun -Kind "environment" -ExitCode 4 -Reason $RecipeReason
}
if ($RecipeExitCode -eq 3) {
    if (-not $RecipeReason) { $RecipeReason = "Arrêt de sécurité avant une action destructive." }
    Complete-LocalRun -Kind "ko" -ExitCode 3 -Reason $RecipeReason
}
if (-not $RecipeReason) {
    $RecipeReason = "Le scénario individus-smoke a échoué (code $RecipeExitCode)."
}
Complete-LocalRun -Kind "ko" -ExitCode $RecipeExitCode -Reason $RecipeReason
