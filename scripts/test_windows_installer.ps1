param(
    [string]$ExpectedCommit = $env:GITHUB_SHA
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$qualificationRoot = Join-Path $env:RUNNER_TEMP 'Qualification Windows Équipe Teamworks'
$installRoot = Join-Path $qualificationRoot 'Installation Teamworks Équipe'
$foreignWorkingDirectory = Join-Path $qualificationRoot 'CWD installation indépendant'
$installLog = Join-Path $qualificationRoot 'installer-install.log'
New-Item -ItemType Directory -Path $foreignWorkingDirectory -Force | Out-Null

$installer = Get-ChildItem (Join-Path $repositoryRoot 'dist/installer/Teamworks-CCNS-*-windows-x64-setup.exe') |
    Select-Object -First 1
if (-not $installer) {
    throw 'Installateur Windows introuvable.'
}

Remove-Item -LiteralPath $installRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $installLog -Force -ErrorAction SilentlyContinue
$installArguments = @(
    '/VERYSILENT',
    '/SUPPRESSMSGBOXES',
    '/NORESTART',
    '/SP-',
    "/DIR=`"$installRoot`"",
    "/LOG=`"$installLog`""
)
$install = Start-Process -FilePath $installer.FullName -ArgumentList $installArguments -Wait -PassThru
if ($install.ExitCode -ne 0) {
    $log = if (Test-Path -LiteralPath $installLog) { Get-Content -LiteralPath $installLog -Raw } else { '' }
    throw "Installation silencieuse en échec avec le code $($install.ExitCode).`n$log"
}

$installedExecutable = Join-Path $installRoot 'Teamworks-CCNS.exe'
$requiredInstalledResources = @(
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
if (-not (Test-Path -LiteralPath $installedExecutable -PathType Leaf)) {
    $log = if (Test-Path -LiteralPath $installLog) { Get-Content -LiteralPath $installLog -Raw } else { '' }
    throw "Exécutable installé absent : $installedExecutable`n$log"
}
foreach ($relative in $requiredInstalledResources) {
    if (-not (Test-Path -LiteralPath (Join-Path $installRoot $relative))) {
        throw "Ressource installée absente : $relative"
    }
}

$buildMarker = Get-Content (Join-Path $installRoot 'BUILD.txt') -Raw
if ($ExpectedCommit -and $buildMarker -notmatch [regex]::Escape($ExpectedCommit)) {
    throw "L'installation ne référence pas le commit construit $ExpectedCommit"
}

$originalPythonHome = $env:PYTHONHOME
$originalPythonPath = $env:PYTHONPATH
$originalPath = $env:PATH
$filteredPath = @(
    $originalPath -split ';' |
        Where-Object { $_ -and $_ -notmatch '(?i)python' -and $_ -notmatch '(?i)hostedtoolcache' }
) -join ';'

$stdout = Join-Path $qualificationRoot 'installer-launch.stdout.log'
$stderr = Join-Path $qualificationRoot 'installer-launch.stderr.log'
$alive = $false
$gracefulClose = $false
$process = $null
try {
    Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    $env:PATH = $filteredPath

    $process = Start-Process `
        -FilePath $installedExecutable `
        -WorkingDirectory $foreignWorkingDirectory `
        -PassThru `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr

    Start-Sleep -Seconds 12
    $process.Refresh()
    if ($process.HasExited) {
        $out = if (Test-Path $stdout) { Get-Content $stdout -Raw } else { '' }
        $err = if (Test-Path $stderr) { Get-Content $stderr -Raw } else { '' }
        throw "L'exécutable installé s'est arrêté prématurément avec le code $($process.ExitCode).`nSTDOUT:`n$out`nSTDERR:`n$err"
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
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        $process.WaitForExit()
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

$uninstaller = Join-Path $installRoot 'unins000.exe'
if (-not (Test-Path -LiteralPath $uninstaller -PathType Leaf)) {
    throw "Désinstalleur absent : $uninstaller"
}
$uninstall = Start-Process `
    -FilePath $uninstaller `
    -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') `
    -Wait `
    -PassThru
if ($uninstall.ExitCode -ne 0) {
    throw "Désinstallation silencieuse en échec avec le code $($uninstall.ExitCode)."
}
if (Test-Path -LiteralPath $installedExecutable) {
    throw "L'exécutable est encore présent après désinstallation."
}

$report = [ordered]@{
    status = 'ok'
    commit = $ExpectedCommit
    installer = $installer.FullName
    install_directory = $installRoot
    install_path_contains_space = $installRoot.Contains(' ')
    install_path_contains_unicode = $installRoot.Contains('É')
    working_directory = $foreignWorkingDirectory
    required_resources = $requiredInstalledResources
    build_marker = $buildMarker.Trim()
    executable_alive_after_12_seconds = $alive
    graceful_close = $gracefulClose
    pythonhome_cleared_during_launch = $true
    pythonpath_cleared_during_launch = $true
    uninstall_exit_code = $uninstall.ExitCode
    executable_removed_after_uninstall = -not (Test-Path -LiteralPath $installedExecutable)
}

$reportPath = Join-Path $repositoryRoot 'windows-release-installer.json'
$report | ConvertTo-Json -Depth 5 | Set-Content -Path $reportPath -Encoding utf8
$report | ConvertTo-Json -Depth 5 | Write-Host
Write-Host 'Qualification installateur réussie : installation, lancement hors CWD et désinstallation vérifiés.'
