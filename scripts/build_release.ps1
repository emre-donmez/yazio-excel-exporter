param(
    [string]$Name = "yazio-exporter",
    [string]$EntryPoint = "main.py",
    [string]$DistPath = "release",
    [string]$WorkPath = "build-release",
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path -LiteralPath $EntryPoint)) {
    throw "Entry point not found: $EntryPoint"
}

Write-Host "Building $Name.exe..."

$excludedModules = @(
    "IPython",
    "matplotlib",
    "numpy",
    "PyQt5",
    "PIL",
    "scipy",
    "pandas",
    "pytest",
    "sphinx",
    "jedi",
    "pygments",
    "zmq",
    "notebook",
    "tkinter",
    "black"
)

$pyInstallerArgs = @(
    "-m", "PyInstaller",
    "--onefile",
    "--name", $Name,
    "--noconfirm",
    "--workpath", $WorkPath,
    "--distpath", $DistPath,
    "--specpath", $WorkPath
)

foreach ($module in $excludedModules) {
    $pyInstallerArgs += @("--exclude-module", $module)
}

$pyInstallerArgs += $EntryPoint

python @pyInstallerArgs

$exePath = Join-Path $DistPath "$Name.exe"
if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Build completed, but executable was not found: $exePath"
}

if (-not $SkipSmokeTest) {
    Write-Host "Running smoke test..."
    & $exePath --help | Out-Null
}

$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $exePath
$size = (Get-Item -LiteralPath $exePath).Length

Write-Host ""
Write-Host "Build complete:"
Write-Host "  File: $exePath"
Write-Host "  Size: $size bytes"
Write-Host "  SHA256: $($hash.Hash)"
