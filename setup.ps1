# All For One - one-time setup for Windows.
# Easiest: double-click setup.bat. Or in PowerShell, from the project folder:
#     powershell -ExecutionPolicy Bypass -File setup.ps1 [-TensorRT | -NoTensorRT]
# Creates .venv (a private Python 3.12 environment for the game), installs the pinned
# packages, picks the CUDA (NVIDIA) or CPU build of PyTorch and downloads the models.
# If Python 3.12 is missing it offers to install it with winget.
param([switch]$TensorRT, [switch]$NoTensorRT)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Step($text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Check($what) {
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $what" -ForegroundColor Red; exit 1 }
}

$TorchVersion = "torch==2.14.1", "torchvision==0.29.1"

Step "1/6 Looking for Python 3.12"
# The game needs exactly Python 3.12: newer versions do not have packages for
# mediapipe / PyTorch yet. Other Python versions on the computer are left alone.
$Is312 = "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)"
function Find-Python312 {
    $default = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"   # python.org / winget
    foreach ($cand in @(@("py", "-3.12"), @("python"), @("python3"), @($default))) {
        try {
            $exe, $rest = $cand
            & $exe @rest -c $Is312 2>$null
            if ($LASTEXITCODE -eq 0) { return , $cand }
        } catch { }
    }
    return $null
}
$py = Find-Python312
if (-not $py -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Python 3.12 is not installed. It can be added next to any other Python versions."
    $answer = Read-Host "Install Python 3.12 now with winget? [y/N]"
    if ($answer -match '^[yY]') {
        winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements
        $py = Find-Python312
    }
}
if (-not $py) {
    Write-Host "Python 3.12 not found." -ForegroundColor Red
    Write-Host "Install it from https://www.python.org/downloads/ (3.12.x), or run:" -ForegroundColor Red
    Write-Host "    winget install -e --id Python.Python.3.12" -ForegroundColor Red
    Write-Host "then run the setup again." -ForegroundColor Red
    exit 1
}
$exe, $rest = $py
& $exe @rest --version

Step "2/6 Creating the environment in .venv"
if (Test-Path ".venv\Scripts\python.exe") {
    & ".venv\Scripts\python.exe" -c $Is312 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host ".venv was made with another Python version - rebuilding it with Python 3.12"
        Remove-Item -Recurse -Force ".venv"
    }
}
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
