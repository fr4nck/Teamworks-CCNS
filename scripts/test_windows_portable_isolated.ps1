[CmdletBinding()]
param(
    [string]$PackageDirectory = "",
    [string]$ExpectedCommit = $env:GITHUB_SHA,
    [ValidateRange(10, 180)][int]$StartupTimeoutSeconds = 45
)

$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "Cette qualification exige Windows et une session interactive."
}

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
if (-not (Test-Path -LiteralPath (Join-Path $repositoryRoot ".git"))) {
    throw "Le script doit rester dans le dossier scripts du depot."
}

if ([string]::IsNullOrWhiteSpace($PackageDirectory)) {
    $sourcePackage = Join-Path $repositoryRoot "dist\Teamworks-CCNS"
}
else {
    $sourcePackage = (Resolve-Path -LiteralPath $PackageDirectory).Path
}

if (-not (Test-Path -LiteralPath $sourcePackage -PathType Container)) {
    throw "Paquet portable absent : $sourcePackage. Construire ou extraire le paquet avant ce test."
}

$sourceExe = Join-Path $sourcePackage "Teamworks-CCNS.exe"
if (-not (Test-Path -LiteralPath $sourceExe -PathType Leaf)) {
    throw "Executable absent du paquet portable : $sourceExe"
}

# Un nom de dossier avec espace ET caractere Unicode, sans modifier le checkout.
$runName = "Teamworks Portable " + [char]0x00C9 + "quipe " + [Guid]::NewGuid().ToString("N")
$qualificationRoot = Join-Path ([System.IO.Path]::GetTempPath()) $runName
$checkoutPrefix = $repositoryRoot.TrimEnd([char[]]@("\", "/")) + [System.IO.Path]::DirectorySeparatorChar

if ($qualificationRoot.StartsWith($checkoutPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Le dossier temporaire est situe dans le depot : qualification refusee."
}

$portableRoot = Join-Path $qualificationRoot "Paquet isole"
$foreignWorkingDirectory = Join-Path $qualificationRoot "CWD hors checkout"
New-Item -ItemType Directory -Path $qualificationRoot -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path $portableRoot -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path $foreignWorkingDirectory -ErrorAction Stop | Out-Null

Write-Host "Copie de qualification : $qualificationRoot"

# On lit le paquet existant. Aucun renommage, deplacement ou nettoyage du code source.
foreach ($entry in @(Get-ChildItem -LiteralPath $sourcePackage -Force)) {
    Copy-Item -LiteralPath $entry.FullName -Destination $portableRoot -Recurse -Force -ErrorAction Stop
}

$portableExe = Join-Path $portableRoot "Teamworks-CCNS.exe"
$requiredResources = @(
    "Teamworks-CCNS.exe",
    "BUILD.txt",
    "VERSION",
    "Versions.txt",
    "Static/Databases/Defaut.dat",
    "Static/Databases/Textes.dat",
    "Static/Databases/Villes.db3",
    "Static/Documents",
    "Static/Exemples",
    "Static/Images"
)

foreach ($relative in $requiredResources) {
    if (-not (Test-Path -LiteralPath (Join-Path $portableRoot $relative))) {
        throw "Ressource absente dans la copie isolee : $relative"
    }
}

$buildMarker = Get-Content -LiteralPath (Join-Path $portableRoot "BUILD.txt") -Raw
if ($ExpectedCommit -and $buildMarker -notmatch [regex]::Escape($ExpectedCommit)) {
    throw "Le BUILD.txt du paquet ne correspond pas au commit attendu : $ExpectedCommit"
}

function Read-TestLog {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return ""
    }
    try {
        return [string](Get-Content -LiteralPath $Path -Raw -ErrorAction Stop)
    }
    catch {
        return ""
    }
}

function Invoke-IsolatedLaunch {
    param(
        [int]$Round,
        [string]$Executable,
        [string]$WorkingDirectory,
        [string]$LogDirectory,
        [int]$TimeoutSeconds
    )

    $stdout = Join-Path $LogDirectory ("launch-" + $Round + ".stdout.log")
    $stderr = Join-Path $LogDirectory ("launch-" + $Round + ".stderr.log")
    $process = $null

    try {
        $process = Start-Process -FilePath $Executable -WorkingDirectory $WorkingDirectory -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
        $window = [IntPtr]::Zero
        $emailMarker = $false

        do {
            Start-Sleep -Milliseconds 500
            $process.Refresh()

            if ($process.HasExited) {
                throw "Demarrage $Round : arret premature (code $($process.ExitCode)). STDOUT: $(Read-TestLog $stdout) STDERR: $(Read-TestLog $stderr)"
            }

            $window = $process.MainWindowHandle
            $emailMarker = ([string](Read-TestLog -Path $stdout)).Contains("TEAMWORKS_PACKAGE_EMAIL_IMPORT_OK")
        } while (($window -eq [IntPtr]::Zero -or -not $emailMarker) -and [DateTime]::UtcNow -lt $deadline)

        if ($window -eq [IntPtr]::Zero -or -not $emailMarker) {
            throw "Demarrage $Round : fenetre ou marqueur Email absent avant $TimeoutSeconds secondes. STDOUT: $(Read-TestLog $stdout) STDERR: $(Read-TestLog $stderr)"
        }

        $process.Refresh()
        if ($process.HasExited) {
            throw "Demarrage $Round : application fermee avant le test de fermeture."
        }

        if (-not $process.CloseMainWindow()) {
            throw "Demarrage $Round : CloseMainWindow refuse."
        }
        if (-not $process.WaitForExit(10000)) {
            throw "Demarrage $Round : fermeture non terminee apres 10 secondes."
        }

        return [pscustomobject]@{
            round = $Round
            window_detected = $true
            email_import_marker = $true
            graceful_close = $true
            exit_code = $process.ExitCode
            stdout = $stdout
            stderr = $stderr
        }
    }
    finally {
        if ($null -ne $process) {
            try {
                $process.Refresh()
                if (-not $process.HasExited) {
                    Stop-Process -Id $process.Id -Force -ErrorAction Stop
                    $process.WaitForExit()
                }
            }
            catch {
                Write-Warning "Impossible de terminer le processus du test $Round : $($_.Exception.Message)"
            }
            $process.Dispose()
        }
    }
}

# L'environnement est reduit uniquement pour les processus de test.
$originalPath = $env:PATH
$originalPythonHome = $env:PYTHONHOME
$originalPythonPath = $env:PYTHONPATH
$originalSmokeEmail = $env:TEAMWORKS_PACKAGE_SMOKE_EMAIL
$results = @()

try {
    $env:PATH = (@($originalPath -split ";" | Where-Object {
        $_ -and $_ -notmatch "(?i)python" -and $_ -notmatch "(?i)hostedtoolcache"
    }) -join ";")
    Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    $env:TEAMWORKS_PACKAGE_SMOKE_EMAIL = "1"

    foreach ($round in @(1, 2)) {
        Write-Host "Qualification Windows : demarrage $round/2"
        $results += Invoke-IsolatedLaunch -Round $round -Executable $portableExe -WorkingDirectory $foreignWorkingDirectory -LogDirectory $qualificationRoot -TimeoutSeconds $StartupTimeoutSeconds
    }
}
finally {
    $env:PATH = $originalPath
    if ($null -eq $originalPythonHome) {
        Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONHOME = $originalPythonHome
    }
    if ($null -eq $originalPythonPath) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONPATH = $originalPythonPath
    }
    if ($null -eq $originalSmokeEmail) {
        Remove-Item Env:TEAMWORKS_PACKAGE_SMOKE_EMAIL -ErrorAction SilentlyContinue
    }
    else {
        $env:TEAMWORKS_PACKAGE_SMOKE_EMAIL = $originalSmokeEmail
    }
}

foreach ($folder in @("teamworks", "domain", "application", "infrastructure")) {
    if (-not (Test-Path -LiteralPath (Join-Path $repositoryRoot $folder) -PathType Container)) {
        throw "Dossier source absent apres qualification : $folder"
    }
}

$report = [ordered]@{
    status = "PASS"
    level = "portable startup smoke - not a functional Windows UI recipe"
    qualification_directory = $qualificationRoot
    source_package = $sourcePackage
    isolated_package = $portableRoot
    external_working_directory = $foreignWorkingDirectory
    unicode_and_spaces_in_path = ($portableRoot.Contains([char]0x00C9) -and $portableRoot.Contains(" "))
    original_sources_unchanged_by_script = $true
    pythonhome_and_pythonpath_cleared_during_launch = $true
    expected_commit = $ExpectedCommit
    build_marker = $buildMarker.Trim()
    launches = $results
}

$reportPath = Join-Path $qualificationRoot "qualification-portable.json"
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Host ""
Write-Host "PASS : 2 ouvertures de fenetre, imports Email et fermetures propres."
Write-Host "Rapport : $reportPath"
Write-Host "Copie temporaire conservee pour examen ; aucun dossier du depot renomme."
