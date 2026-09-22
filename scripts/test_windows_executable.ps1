param(
    [string]$ExpectedCommit = $env:GITHUB_SHA
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$sourcePackage = Join-Path $repositoryRoot 'dist/Teamworks-CCNS'
$sourceExecutable = Join-Path $sourcePackage 'Teamworks-CCNS.exe'
if (-not (Test-Path -LiteralPath $sourceExecutable -PathType Leaf)) {
    throw "Exécutable introuvable : $sourceExecutable"
}

$qualificationRoot = Join-Path $env:RUNNER_TEMP 'Qualification Windows Équipe Teamworks'
$portableRoot = Join-Path $qualificationRoot 'Portable Teamworks'
$foreignWorkingDirectory = Join-Path $qualificationRoot 'Dossier courant étranger au checkout'
Remove-Item -LiteralPath $qualificationRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $portableRoot -Force | Out-Null
New-Item -ItemType Directory -Path $foreignWorkingDirectory -Force | Out-Null
Copy-Item -Path (Join-Path $sourcePackage '*') -Destination $portableRoot -Recurse -Force

$portableExecutable = Join-Path $portableRoot 'Teamworks-CCNS.exe'
$requiredResources = @(
    'BUILD.txt',
    'VERSION',
    'Versions.txt',
    'Static/Databases/Defaut.dat',
    'Static/Databases/Textes.dat',
    'Static/Databases/Villes.db3',
    'Static/Documents',
    'Static/Exemples',
    'Static/Images'
)
foreach ($relative in $requiredResources) {
    $target = Join-Path $portableRoot $relative
    if (-not (Test-Path -LiteralPath $target)) {
        throw "Ressource requise absente du paquet isolé : $relative"
    }
}

$buildMarker = Get-Content (Join-Path $portableRoot 'BUILD.txt') -Raw
if ($ExpectedCommit -and $buildMarker -notmatch [regex]::Escape($ExpectedCommit)) {
    throw "BUILD.txt ne référence pas le commit construit $ExpectedCommit"
}

function Invoke-TeamworksProbe {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $safeLabel = $Label -replace '[^A-Za-z0-9_-]', '_'
    $stdout = Join-Path $qualificationRoot "$safeLabel.stdout.log"
    $stderr = Join-Path $qualificationRoot "$safeLabel.stderr.log"
    Remove-Item $stdout, $stderr -ErrorAction SilentlyContinue

    $process = Start-Process `
        -FilePath $Executable `
        -WorkingDirectory $WorkingDirectory `
        -PassThru `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr

    $alive = $false
    $gracefulClose = $false
    try {
        Start-Sleep -Seconds 12
        $process.Refresh()
        if ($process.HasExited) {
            $out = if (Test-Path $stdout) { Get-Content $stdout -Raw } else { '' }
            $err = if (Test-Path $stderr) { Get-Content $stderr -Raw } else { '' }
            throw "Teamworks-CCNS s'est arrêté prématurément avec le code $($process.ExitCode).`nSTDOUT:`n$out`nSTDERR:`n$err"
        }
        $alive = $true

        try {
            if ($process.CloseMainWindow()) {
                $gracefulClose = $process.WaitForExit(10000)
            }
        }
        catch {
            $gracefulClose = $false
        }
    }
    finally {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force
            $process.WaitForExit()
        }
    }

    return [ordered]@{
        label = $Label
        alive_after_12_seconds = $alive
        graceful_close = $gracefulClose
        exit_code = $process.ExitCode
        stdout = $stdout
        stderr = $stderr
    }
}

$originalPythonHome = $env:PYTHONHOME
$originalPythonPath = $env:PYTHONPATH
$originalPath = $env:PATH
$pythonPathEntries = @(
    $originalPath -split ';' |
        Where-Object { $_ -and ($_ -match '(?i)python' -or $_ -match '(?i)hostedtoolcache') }
)
$filteredPath = @(
    $originalPath -split ';' |
        Where-Object { $_ -and $_ -notmatch '(?i)python' -and $_ -notmatch '(?i)hostedtoolcache' }
) -join ';'

$sourceDirectories = @('teamworks', 'domain', 'application', 'infrastructure')
$hiddenSources = @()
$siteDataDirectory = Join-Path $env:ProgramData 'teamworks'
$siteDataExistedBefore = Test-Path -LiteralPath $siteDataDirectory
$firstProbe = $null
$secondProbe = $null

try {
    Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    $env:PATH = $filteredPath

    foreach ($name in $sourceDirectories) {
        $source = Join-Path $repositoryRoot $name
        if (Test-Path -LiteralPath $source -PathType Container) {
            $hiddenName = ".$name.tw10-04-source-hidden"
            $hidden = Join-Path $repositoryRoot $hiddenName
            Rename-Item -LiteralPath $source -NewName $hiddenName
            $hiddenSources += [ordered]@{ source = $source; hidden = $hidden }
        }
    }

    $firstProbe = Invoke-TeamworksProbe `
        -Executable $portableExecutable `
        -WorkingDirectory $foreignWorkingDirectory `
        -Label 'portable-first-launch'

    $secondProbe = Invoke-TeamworksProbe `
        -Executable $portableExecutable `
        -WorkingDirectory $foreignWorkingDirectory `
        -Label 'portable-second-launch'
}
finally {
    foreach ($item in @($hiddenSources) | Select-Object -Last 100) {
        if (Test-Path -LiteralPath $item.hidden -PathType Container) {
            Rename-Item -LiteralPath $item.hidden -NewName (Split-Path -Leaf $item.source)
        }
    }

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
}

$report = [ordered]@{
    status = 'ok'
    commit = $ExpectedCommit
    source_package = $sourcePackage
    isolated_package = $portableRoot
    working_directory = $foreignWorkingDirectory
    package_path_contains_space = $portableRoot.Contains(' ')
    package_path_contains_unicode = $portableRoot.Contains('É')
    checkout_source_directories_hidden_during_launch = @($hiddenSources).Count -eq $sourceDirectories.Count
    pythonhome_cleared_during_launch = $true
    pythonpath_cleared_during_launch = $true
    python_path_entries_removed = $pythonPathEntries
    programdata_teamworks_existed_before = $siteDataExistedBefore
    required_resources = $requiredResources
    build_marker = $buildMarker.Trim()
    first_launch = $firstProbe
    second_launch = $secondProbe
}

$reportPath = Join-Path $repositoryRoot 'windows-release-portable.json'
$report | ConvertTo-Json -Depth 6 | Set-Content -Path $reportPath -Encoding utf8
$report | ConvertTo-Json -Depth 6 | Write-Host
Write-Host "Qualification portable réussie : exécutable lancé hors checkout depuis un chemin avec espaces et Unicode."
