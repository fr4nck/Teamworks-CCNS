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
        throw "Teamworks-CCNS s'est arrêté prématurément avec le code $($process.ExitCode).`nSTDOUT:`n$out`nSTDERR:`n$err"
    }

    Write-Host "Smoke test réussi : l'application est restée active pendant 12 secondes."
}
finally {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
        $process.WaitForExit()
    }
}
