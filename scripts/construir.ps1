# Construye el ejecutable de Windows con PyInstaller (receta: viviani.spec).
#
# Uso, desde cualquier carpeta:
#     .\scripts\construir.ps1                 # los dos modos
#     .\scripts\construir.ps1 -Modo onedir    # carpeta con el .exe (abre rápido)
#     .\scripts\construir.ps1 -Modo onefile   # un solo .exe (más fácil de enviar)
#
# Resultado en dist\ (no se sube a git):
#     dist\PerimetroViviani\PerimetroViviani.exe   (onedir)
#     dist\PerimetroViviani-onedir.zip             (onedir comprimido)
#     dist\PerimetroViviani.exe                    (onefile)
param(
    [ValidateSet("onedir", "onefile", "ambos")]
    [string]$Modo = "ambos"
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
$python = Join-Path $raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "No existe .venv. Ejecute primero .\scripts\ejecutar.ps1 para crearlo."
}

Write-Host "Ejecutando las pruebas antes de construir..."
& $python -m unittest
if ($LASTEXITCODE -ne 0) { throw "Hay pruebas que fallan: no se construye." }

$modos = if ($Modo -eq "ambos") { @("onedir", "onefile") } else { @($Modo) }
foreach ($m in $modos) {
    Write-Host "`nConstruyendo modo $m ..."
    $env:VIVIANI_MODO = $m
    $inicio = Get-Date
    & $python -m PyInstaller viviani.spec --noconfirm --clean `
        --distpath dist --workpath "build\$m" --log-level WARN
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller falló en modo $m." }
    $segundos = [math]::Round(((Get-Date) - $inicio).TotalSeconds)

    if ($m -eq "onedir") {
        $carpeta = "dist\PerimetroViviani"
        $mb = (Get-ChildItem $carpeta -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
        $zip = "dist\PerimetroViviani-onedir.zip"
        if (Test-Path $zip) { Remove-Item $zip }
        Compress-Archive -Path $carpeta -DestinationPath $zip
        $mbZip = (Get-Item $zip).Length / 1MB
        Write-Host ("Listo en {0} s: {1} ({2:N1} MB), comprimido {3:N1} MB" -f $segundos, $carpeta, $mb, $mbZip)
    } else {
        $mb = (Get-Item "dist\PerimetroViviani.exe").Length / 1MB
        Write-Host ("Listo en {0} s: dist\PerimetroViviani.exe ({1:N1} MB)" -f $segundos, $mb)
    }
}
Remove-Item Env:\VIVIANI_MODO
