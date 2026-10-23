$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$jdkFolder = Get-ChildItem -LiteralPath "$projectRoot\.tools\jdk" -Directory | Select-Object -First 1
$jdkBin = Join-Path $jdkFolder.FullName 'bin'
$platform = Join-Path $projectRoot '.tools\sdk\platforms\android-35\android.jar'
$buildTools = Join-Path $projectRoot '.tools\sdk\build-tools\android-15'
$buildDir = Join-Path $projectRoot 'android\app\build'
$javaSource = Join-Path $projectRoot 'android\app\src\main'
New-Item -ItemType Directory -Force "$buildDir\gen","$buildDir\classes","$buildDir\dex","$projectRoot\artifacts" | Out-Null
function Check-Exit { if ($LASTEXITCODE -ne 0) { throw "Build command failed: $LASTEXITCODE" } }
& "$buildTools\aapt.exe" package -f -m -J "$buildDir\gen" -M "$javaSource\AndroidManifest.xml" -S "$javaSource\res" -A "$projectRoot\web" -I $platform -F "$buildDir\unsigned.apk" --min-sdk-version 26 --target-sdk-version 35
Check-Exit
$sources = @(Get-ChildItem "$javaSource\java","$buildDir\gen" -Recurse -Filter *.java | ForEach-Object { $_.FullName })
& "$jdkBin\javac.exe" -encoding UTF-8 -source 8 -target 8 -bootclasspath $platform -d "$buildDir\classes" $sources
Check-Exit
& "$jdkBin\jar.exe" cf "$buildDir\classes.jar" -C "$buildDir\classes" .
Check-Exit
& "$jdkBin\java.exe" -cp "$buildTools\lib\d8.jar" com.android.tools.r8.D8 --min-api 26 --lib $platform --output "$buildDir\dex" "$buildDir\classes.jar"
Check-Exit
& "$jdkBin\jar.exe" uf "$buildDir\unsigned.apk" -C "$buildDir\dex" classes.dex
Check-Exit
& "$buildTools\zipalign.exe" -f 4 "$buildDir\unsigned.apk" "$buildDir\aligned.apk"
Check-Exit
if (-not (Test-Path "$projectRoot\.tools\debug.keystore")) {
  & "$jdkBin\keytool.exe" -genkeypair -keystore "$projectRoot\.tools\debug.keystore" -storepass android -keypass android -alias androiddebugkey -dname 'CN=Beyond The Frame Development' -keyalg RSA -validity 10000
  Check-Exit
}
& "$jdkBin\java.exe" -jar "$buildTools\lib\apksigner.jar" sign --ks "$projectRoot\.tools\debug.keystore" --ks-pass pass:android --out "$projectRoot\artifacts\Beyond-The-Frame-debug.apk" "$buildDir\aligned.apk"
Check-Exit
& "$jdkBin\java.exe" -jar "$buildTools\lib\apksigner.jar" verify --verbose "$projectRoot\artifacts\Beyond-The-Frame-debug.apk"
Check-Exit
Write-Output "APK: $projectRoot\artifacts\Beyond-The-Frame-debug.apk"
