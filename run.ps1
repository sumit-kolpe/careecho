# Launch from any working directory using the project-local environment.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$pythonPath = Join-Path $PSScriptRoot ".venv/Scripts/python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create the environment first: python -m venv .venv; then install the extras listed in README.md.'
}
$env:HF_HOME = Join-Path $PSScriptRoot ".cache/huggingface"
& $pythonPath -m streamlit run app.py
