# setup_env.ps1 - create a virtual environment and install requirements
$venvPath = Join-Path $PSScriptRoot ".venv"
if (-Not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

$pip = Join-Path $venvPath "Scripts\pip.exe"
& $pip install --upgrade pip
& $pip install -r (Join-Path $PSScriptRoot "requirements.txt")
Write-Host "Environment setup complete. Use: $venvPath\Scripts\Activate.ps1 to activate the venv."