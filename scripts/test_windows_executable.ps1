$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repositoryRoot

$executable = Join-Path $repositoryRoot 'dist/Teamworks-CCNS/Teamworks-CCNS.exe'
if (-not (Test-Path $executable)) {
    throw "Exécutable introuvable : $executable"
}

$stdout = Join-Path $repositoryRoot 'teamworks-smoke.stdout.log'
$stderr = Join-Path $repositoryRoot 'teamworks-smoke.stderr.log'
Remove-Item $stdout, $stderr -ErrorAction SilentlyContinue

$env:TEAMWORKS_PACKAGE_SMOKE_EMAIL = '1'

$process = Start-Process `
    -FilePath $executable `
    -WorkingDirectory (Split-Path -Parent $executable) `
    -PassThru `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr

try {
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    $mainWindow = [IntPtr]::Zero

    do {
        Start-Sleep -Milliseconds 500
        $process.Refresh()

        if ($process.HasExited) {
            throw "Teamworks-CCNS s'est ferme avant l'ouverture de sa fenetre."
        }

        $mainWindow = $process.MainWindowHandle
    } while ($mainWindow -eq [IntPtr]::Zero -and [DateTime]::UtcNow -lt $deadline)

    if ($mainWindow -eq [IntPtr]::Zero) {
        throw "Aucune fenetre principale Windows detectee apres 30 secondes."
    }

    Write-Host "Fenetre principale detectee : $mainWindow"

    if ($process.HasExited) {
        $out = if (Test-Path $stdout) { Get-Content $stdout -Raw } else { '' }
        $err = if (Test-Path $stderr) { Get-Content $stderr -Raw } else { '' }
        throw "Teamworks-CCNS s'est arrêté prématurément avec le code $($process.ExitCode). STDOUT: $out STDERR: $err"
    }

    $out = if (Test-Path $stdout) { Get-Content $stdout -Raw } else { '' }
    if ($out -notmatch 'TEAMWORKS_PACKAGE_EMAIL_IMPORT_OK') {
        throw "Le paquet n'a pas confirmé l'import de l'éditeur Email. STDOUT: $out"
    }

    Write-Host "Smoke test réussi : une fenêtre principale Windows a été détectée et l'éditeur Email est importable."
}
finally {
    Remove-Item Env:TEAMWORKS_PACKAGE_SMOKE_EMAIL -ErrorAction SilentlyContinue
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        $process.WaitForExit()
    }
}
