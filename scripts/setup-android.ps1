# Installs build-only tools locally; no emulator or global PATH changes.
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$toolDir=Join-Path $projectRoot '.tools'
New-Item -ItemType Directory -Force $toolDir | Out-Null
if(-not (Test-Path "$toolDir\jdk")) {
  Invoke-WebRequest 'https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse' -OutFile "$toolDir\jdk.zip"
  Expand-Archive -LiteralPath "$toolDir\jdk.zip" -DestinationPath "$toolDir\jdk"
}
if(-not (Test-Path "$toolDir\sdk\platforms\android-35\android.jar")) {
  Invoke-WebRequest 'https://dl.google.com/android/repository/platform-35_r02.zip' -OutFile "$toolDir\platform.zip"
  Expand-Archive -LiteralPath "$toolDir\platform.zip" -DestinationPath "$toolDir\sdk\platforms" -Force
}
if(-not (Test-Path "$toolDir\sdk\build-tools\android-15\aapt.exe")) {
  Invoke-WebRequest 'https://dl.google.com/android/repository/build-tools_r35_windows.zip' -OutFile "$toolDir\build-tools.zip"
  Expand-Archive -LiteralPath "$toolDir\build-tools.zip" -DestinationPath "$toolDir\sdk\build-tools" -Force
}
Write-Output 'Ready. Run powershell -ExecutionPolicy Bypass -File scripts/build-android.ps1'
