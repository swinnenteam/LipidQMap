<#
Build:
.\build-windows.ps1 win-build

Sign everything:
.\build-windows.ps1 win-sign -PfxPath "C:\certs\yourcert.pfx" -PfxPassword "*****"

Verify the main EXE:
.\build-windows.ps1 win-verify

Zip for users:
.\build-windows.ps1 win-release
→ dist\LipidQMap-windows.zip + .sha256
#>

param(
  [Parameter(Mandatory=$true, Position=0)]
  [ValidateSet(
    'clean','clean-pyc','setup','deps','ui','res','run',
    'win-build','win-sign','win-verify','win-zip','win-release'
  )]
  [string]$Task,

  # Signing options (only needed for win-sign)
  [string]$PfxPath,
  [string]$PfxPassword,
  # RFC3161 timestamp (DigiCert default)
  [string]$TimestampUrl = 'http://timestamp.digicert.com'
)

# --- Config ---
$AppName      = 'LipidQMap'
$Spec         = 'win-app.spec'
$DistRoot     = 'dist'
$BuildDir     = 'build'
$Venv         = 'venv'
$PythonExe    = Join-Path $Venv 'Scripts\python.exe'
$PipExe       = Join-Path $Venv 'Scripts\pip.exe'
$PyInstaller  = "$PythonExe -m PyInstaller"

# One-folder output goes here:
$AppDir       = Join-Path $DistRoot $AppName
$MainExe      = Join-Path $AppDir "$AppName.exe"

# Release artifacts
$ZipPath      = Join-Path $DistRoot "$AppName-windows.zip"
$ShaPath      = "$ZipPath.sha256"
$RequirementsDev = 'requirements\dev.txt'

function Ensure-Venv {
  if (-not (Test-Path $PythonExe)) {
    Write-Host "Creating venv..."
    py -3.12 -m venv $Venv
  }
}

function Task-CleanPyc {
  Get-ChildItem -Recurse -Include *.pyc,*.pyo | Remove-Item -Force -ErrorAction SilentlyContinue
  Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

function Task-Clean {
  Task-CleanPyc
  if (Test-Path $BuildDir) { Remove-Item $BuildDir -Recurse -Force }
  if (Test-Path $DistRoot) { Remove-Item $DistRoot -Recurse -Force }
}

function Task-Setup {
  Task-Clean
  if (Test-Path $Venv) { Remove-Item $Venv -Recurse -Force }
  py -3.12 -m venv $Venv
  & $PipExe install -r $RequirementsDev
}

function Task-Deps {
  Ensure-Venv
  & $PipExe install -r $RequirementsDev
}

function Task-UI {
  Ensure-Venv
  & $PythonExe -m PySide6.scripts.pyside_tool uic --from-imports `
    resources/views/MsiImportDialog.ui          -o app/generated/MsiImportDialog_ui.py
  & $PythonExe -m PySide6.scripts.pyside_tool uic --from-imports `
    resources/views/MsiSaveDialog.ui            -o app/generated/MsiSaveDialog_ui.py
  & $PythonExe -m PySide6.scripts.pyside_tool uic --from-imports `
    resources/views/MsiMainWindow.ui            -o app/generated/MsiMainWindow_ui.py
  & $PythonExe -m PySide6.scripts.pyside_tool uic --from-imports `
    resources/views/MsiAboutDialog.ui           -o app/generated/MsiAboutDialog_ui.py
  & $PythonExe -m PySide6.scripts.pyside_tool uic --from-imports `
    resources/views/MsiSettingsDialog.ui        -o app/generated/MsiSettingsDialog_ui.py
  & $PythonExe -m PySide6.scripts.pyside_tool uic --from-imports `
    resources/views/MsiStandardCalculatorDialog.ui -o app/generated/MsiStandardCalculator_ui.py
}

function Task-Res {
  Ensure-Venv
  & $PythonExe -m PySide6.scripts.pyside_tool rcc -compress 9 `
    -o app/generated/resources_rc.py resources/resources.qrc
}

function Task-Run {
  $env:PYTHONPATH = (Get-Location).Path
  Ensure-Venv
  & $PythonExe app
}

function Task-WinBuild {
  Task-Clean
  Ensure-Venv
  & $PyInstaller $Spec
  if (-not (Test-Path $MainExe)) {
    throw "Build failed: $MainExe not found."
  }
  Write-Host "Built folder: $AppDir"
}

function Find-SignTool {
  $sdkRoots = @(
    "${env:ProgramFiles(x86)}\Windows Kits\10\bin",
    "${env:ProgramFiles(x86)}\Windows Kits\11\bin"
  ) | Where-Object { Test-Path $_ }

  foreach ($root in $sdkRoots) {
    $cand = Get-ChildItem $root -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cand) { return $cand.FullName }
  }
  return $null
}

function Task-WinSign {
  if (-not (Test-Path $AppDir)) { throw "Missing $AppDir. Run 'win-build' first." }
  if (-not $PfxPath -or -not (Test-Path $PfxPath)) {
    throw "Provide -PfxPath path\to\cert.pfx for signing."
  }
  $signtool = Find-SignTool
  if (-not $signtool) { throw "signtool.exe not found. Install Windows SDK." }

  # Sign ALL EXEs and DLLs inside the folder
  $files = Get-ChildItem $AppDir -Recurse -Include *.exe,*.dll
  foreach ($f in $files) {
    & $signtool sign `
      /f $PfxPath `
      /p $PfxPassword `
      /fd SHA256 `
      /td SHA256 `
      /tr $TimestampUrl `
      "$($f.FullName)" | Write-Host
  }
  Write-Host "Signed binaries in: $AppDir"
}

function Task-WinVerify {
  if (-not (Test-Path $MainExe)) { throw "Missing $MainExe. Build first." }
  $signtool = Find-SignTool
  if (-not $signtool) { throw "signtool.exe not found. Install Windows SDK." }
  & $signtool verify /pa /v "$MainExe" | Write-Host
}

function Task-WinZip {
  if (-not (Test-Path $AppDir)) { throw "Missing $AppDir. Build first." }
  if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [System.IO.Compression.ZipFile]::CreateFromDirectory($AppDir, $ZipPath)
  Write-Host "Created: $ZipPath"
}

function Task-WinRelease {
  Task-WinZip
  if (Test-Path $ShaPath) { Remove-Item $ShaPath -Force }
  $sha = Get-FileHash -Path $ZipPath -Algorithm SHA256
  "$($sha.Hash)  $ZipPath" | Out-File -Encoding ascii $ShaPath
  Write-Host "Release artifacts:"
  Write-Host "  - $ZipPath"
  Write-Host "  - $ShaPath"
}

switch ($Task) {
  'clean'       { Task-Clean }
  'clean-pyc'   { Task-CleanPyc }
  'setup'       { Task-Setup }
  'deps'        { Task-Deps }
  'ui'          { Task-UI }
  'res'         { Task-Res }
  'run'         { Task-Run }
  'win-build'   { Task-WinBuild }
  'win-sign'    { Task-WinSign }
  'win-verify'  { Task-WinVerify }
  'win-zip'     { Task-WinZip }
  'win-release' { Task-WinRelease }
}
