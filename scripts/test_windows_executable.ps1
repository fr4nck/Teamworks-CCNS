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
    Start-Sleep -Seconds 12

    if ($process.HasExited) {
        $out = if (Test-Path $stdout) { Get-Content $stdout -Raw } else { '' }
        $err = if (Test-Path $stderr) { Get-Content $stderr -Raw } else { '' }
        throw "Teamworks-CCNS s'est arrêté prématurément avec le code $($process.ExitCode). STDOUT: $out STDERR: $err"
    }

    $out = if (Test-Path $stdout) { Get-Content $stdout -Raw } else { '' }
    if ($out -notmatch 'TEAMWORKS_PACKAGE_EMAIL_IMPORT_OK') {
        throw "Le paquet n'a pas confirmé l'import de l'éditeur Email. STDOUT: $out"
    }

    Write-Host "Smoke test réussi : l'application est restée active pendant 12 secondes et l'éditeur Email est importable."
}
finally {
    Remove-Item Env:TEAMWORKS_PACKAGE_SMOKE_EMAIL -ErrorAction SilentlyContinue
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        $process.WaitForExit()
    }
}
