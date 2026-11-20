# Prepara el entorno virtual (solo la primera vez) y abre la aplicación.
# Uso, desde cualquier carpeta:   .\scripts\ejecutar.ps1
#        con -Pruebas ejecuta además los tests y el lint antes de abrir.
param([switch]$Pruebas)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

$python = Join-Path $raiz ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creando el entorno virtual en .venv ..."
    python -m venv .venv
    & $python -m pip install --only-binary :all: -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias." }
}

if ($Pruebas) {
    & $python -m unittest
    if ($LASTEXITCODE -ne 0) { throw "Hay pruebas que fallan." }
    & $python -m ruff check .
    if ($LASTEXITCODE -ne 0) { throw "ruff encontró problemas." }
}

& $python viviani_app.py
