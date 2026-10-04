# All For One - one-time setup for Windows.
# Easiest: double-click setup.bat. Or in PowerShell, from the project folder:
#     powershell -ExecutionPolicy Bypass -File setup.ps1 [-TensorRT | -NoTensorRT]
# Creates .venv (a private Python environment for the game), installs the pinned
# packages, picks the CUDA (NVIDIA) or CPU build of PyTorch and downloads the models.
param([switch]$TensorRT, [switch]$NoTensorRT)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Step($text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Check($what) {
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $what" -ForegroundColor Red; exit 1 }
}

$TorchVersion = "torch==2.14.1", "torchvision==0.29.1"

Step "1/6 Looking for Python 3.10 or newer"
$py = $null
foreach ($cand in @(@("py", "-3.12"), @("py", "-3.11"), @("py", "-3.10"), @("python"))) {
    try {
        $exe, $rest = $cand
        & $exe @rest -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $py = $cand; break }
    } catch { }
}
if (-not $py) {
    Write-Host "Python 3.10+ not found." -ForegroundColor Red
    Write-Host "Install Python 3.12 from https://www.python.org (tick 'Add to PATH')." -ForegroundColor Red
    exit 1
}
$exe, $rest = $py
& $exe @rest --version

Step "2/6 Creating the environment in .venv"
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $exe @rest -m venv .venv; Check "creating .venv"
} else { Write-Host ".venv already exists - updating it" }
$vpy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $vpy -m pip install --upgrade pip --quiet; Check "upgrading pip"

Step "3/6 Installing PyTorch"
$gpu = $null -ne (Get-Command nvidia-smi -ErrorAction SilentlyContinue)
if ($gpu) {
    Write-Host "NVIDIA GPU found - installing the CUDA build (large download, a few minutes)"
    & $vpy -m pip install @TorchVersion --index-url https://download.pytorch.org/whl/cu130
    Check "installing PyTorch (CUDA)"
} else {
    Write-Host "No NVIDIA GPU - installing the small CPU build"
    & $vpy -m pip install @TorchVersion --index-url https://download.pytorch.org/whl/cpu
    Check "installing PyTorch (CPU)"
}

Step "4/6 Installing the game's packages"
& $vpy -m pip install -r requirements.txt; Check "installing requirements.txt"

Step "5/6 Optional: TensorRT (about 2x faster pose detection)"
$wantTrt = $false
if ($gpu -and -not $NoTensorRT) {
    if ($TensorRT) { $wantTrt = $true }
    else {
        $answer = Read-Host "Install TensorRT and build the engine? Takes ~10 minutes [y/N]"
        $wantTrt = $answer -match '^[yY]'
    }
}
if ($wantTrt) {
    & $vpy -m pip install -r requirements-gpu.txt; Check "installing TensorRT"
    & $vpy export_engine.py; Check "building the TensorRT engine"
} else { Write-Host "skipped (the game works without it)" }

Step "6/6 Downloading the AI models"
& $vpy download_models.py; Check "downloading the models"

Write-Host "`nDone! Start the game with:  run.bat" -ForegroundColor Green
Write-Host "(or: .venv\Scripts\python.exe main.py)" -ForegroundColor Green
