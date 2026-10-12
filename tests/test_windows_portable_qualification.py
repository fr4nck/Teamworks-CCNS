"""Tests du harnais PowerShell avec processus doublé, sans application graphique."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/test_windows_portable_isolated.ps1"
SHELL = shutil.which("pwsh") or shutil.which("powershell")
pytestmark = pytest.mark.skipif(os.name != "nt" or not SHELL, reason="PowerShell Windows requis")


@pytest.mark.parametrize("exit_code,accepted", [(0, True), (7, False)])
def test_portable_qualification_rejects_failed_exit(tmp_path, exit_code, accepted):
    harness = tmp_path / "probe.ps1"
    harness.write_text(r'''
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$tree = [System.Management.Automation.Language.Parser]::ParseFile($args[0], [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Parse failed' }
$functions = $tree.FindAll({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst]}, $false)
foreach ($function in $functions) { Invoke-Expression $function.Extent.Text }
function Start-Sleep { param($Milliseconds) }
function Read-TestLog { param($Path) return 'TEAMWORKS_PACKAGE_EMAIL_IMPORT_OK' }
$script:disposed = $false
$script:stopped = $false
$script:fake = [pscustomobject]@{HasExited=$false; MainWindowHandle=[IntPtr]1; ExitCode=[int]$args[1]; Id=12345}
$script:fake | Add-Member ScriptMethod Refresh {}
$script:fake | Add-Member ScriptMethod CloseMainWindow { return $true }
$script:fake | Add-Member ScriptMethod WaitForExit { $this.HasExited=$true; return $true }
$script:fake | Add-Member ScriptMethod Dispose { $script:disposed=$true }
function Start-Process { return $script:fake }
function Stop-Process { $script:stopped=$true }
$accepted=$false; $errorMessage=''
try {
    $result = Invoke-IsolatedLaunch -Round 1 -Executable fake -WorkingDirectory fake -LogDirectory $args[2] -TimeoutSeconds 10
    $accepted=$true
} catch { $errorMessage=$_.Exception.Message }
@{accepted=$accepted; message=$errorMessage; disposed=$script:disposed; stopped=$script:stopped} | ConvertTo-Json -Compress
''', encoding="utf-8-sig")
    result = subprocess.run([SHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                             str(harness), str(SCRIPT), str(exit_code), str(tmp_path)],
                            capture_output=True, text=True, timeout=20, check=True)
    report = json.loads(result.stdout)
    assert report["accepted"] is accepted
    assert report["disposed"] is True
    assert report["stopped"] is False
    if not accepted:
        assert "7" in report["message"]


def test_empty_build_marker_is_rejected_before_launch(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    for name in ("Teamworks-CCNS.exe", "BUILD.txt", "VERSION", "Versions.txt",
                 "Static/Databases/Defaut.dat", "Static/Databases/Textes.dat",
                 "Static/Databases/Villes.db3"):
        path = package / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    for name in ("Static/Documents", "Static/Exemples", "Static/Images"):
        (package / name).mkdir()
    env = os.environ.copy()
    env["TEMP"] = str(tmp_path)
    env["TMP"] = str(tmp_path)
    result = subprocess.run([SHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                             str(SCRIPT), "-PackageDirectory", str(package), "-ExpectedCommit", ""],
                            capture_output=True, text=True, env=env, timeout=20)
    assert result.returncode != 0
    assert "BUILD.txt vide" in result.stderr
    assert "Qualification Windows : demarrage" not in result.stdout


def test_legacy_entry_point_delegates_without_a_second_probe():
    source = (ROOT / "scripts/test_windows_portable_isolation.ps1").read_text(encoding="utf-8-sig")
    assert 'test_windows_portable_isolated.ps1' in source
    assert "@PSBoundParameters" in source
    assert "Start-Process" not in source
    assert "Remove-Item" not in source


def test_legacy_entry_point_forwards_explicit_parameters(tmp_path):
    legacy = tmp_path / "test_windows_portable_isolation.ps1"
    shutil.copyfile(ROOT / "scripts" / legacy.name, legacy)
    (tmp_path / "test_windows_portable_isolated.ps1").write_text('''
param([string]$ExpectedCommit, [string]$PackageDirectory, [int]$StartupTimeoutSeconds)
@{commit=$ExpectedCommit; package=$PackageDirectory; timeout=$StartupTimeoutSeconds} | ConvertTo-Json -Compress
''', encoding="utf-8-sig")
    result = subprocess.run([SHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                             str(legacy), "-ExpectedCommit", "test-sha",
                             "-PackageDirectory", "chemin avec espaces", "-StartupTimeoutSeconds", "15"],
                            capture_output=True, text=True, timeout=20, check=True)
    assert json.loads(result.stdout) == {"commit": "test-sha", "package": "chemin avec espaces", "timeout": 15}
