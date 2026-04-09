$ErrorActionPreference = "Stop"

$projectDir = "D:\1nottingham\Year4a\FYP\hospital_main_copy\-Heatmap-VRPTW\New_GCN_XYZ"
$pythonExe = "D:\anaconda3\envs\pytorch_gpu\python.exe"
$cacheRoot = "D:\runtime_cache\pytorch_gpu"

if (-not (Test-Path $pythonExe)) {
    throw "python not found: $pythonExe"
}

New-Item -ItemType Directory -Force -Path "$cacheRoot\pip", "$cacheRoot\tmp", "$cacheRoot\mpl" | Out-Null

$env:PIP_CACHE_DIR = "$cacheRoot\pip"
$env:TEMP = "$cacheRoot\tmp"
$env:TMP = "$cacheRoot\tmp"
$env:MPLCONFIGDIR = "$cacheRoot\mpl"

Set-Location $projectDir

Write-Host "Running comparison with:" -ForegroundColor Cyan
Write-Host "  python: $pythonExe"
Write-Host "  project: $projectDir"
Write-Host "  PIP_CACHE_DIR: $env:PIP_CACHE_DIR"
Write-Host "  TEMP: $env:TEMP"

& $pythonExe ".\run_comparison.py"
