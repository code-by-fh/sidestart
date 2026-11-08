# Downloads the exact SDK in .fvmrc and verifies its official SHA-256.
param(
    [string]$SdkDirectory = (Join-Path $env:LOCALAPPDATA 'SideStartSDK')
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$projectDirectory = Split-Path -Parent $PSScriptRoot
$flutterPin = (Get-Content -LiteralPath (Join-Path $projectDirectory '.fvmrc') -Raw | ConvertFrom-Json).flutter
$releaseIndex = Invoke-RestMethod -Uri 'https://storage.googleapis.com/flutter_infra_release/flutter/releases/releases_windows.json'
$matchingRelease = @($releaseIndex.releases | Where-Object { $_.version -eq $flutterPin -and $_.channel -eq 'stable' })
if ($matchingRelease.Count -ne 1) {
    throw "Expected one stable Windows SDK for $flutterPin. Check the official Flutter SDK archive."
}
$flutterRelease = $matchingRelease[0]
$versionDirectory = Join-Path $SdkDirectory $flutterPin
$flutterBinary = Join-Path $versionDirectory 'flutter\bin\flutter.bat'
if (Test-Path -LiteralPath $versionDirectory) {
    throw "SDK target already exists: $versionDirectory. Use the existing SDK or choose another -SdkDirectory."
}
New-Item -ItemType Directory -Path $versionDirectory -Force | Out-Null
$sdkZip = Join-Path $versionDirectory 'flutter-sdk.zip'
Write-Host "Downloading Flutter $flutterPin. The SDK requires several GB of free disk space."
Invoke-WebRequest -Uri ($releaseIndex.base_url + '/' + $flutterRelease.archive) -OutFile $sdkZip -UseBasicParsing
$actualHash = (Get-FileHash -LiteralPath $sdkZip -Algorithm SHA256).Hash
if ($actualHash -ne $flutterRelease.sha256) {
    throw 'SHA-256 verification failed. The downloaded SDK will not be extracted.'
}
Expand-Archive -LiteralPath $sdkZip -DestinationPath $versionDirectory
Remove-Item -LiteralPath $sdkZip
$flutterBinDirectory = Split-Path -Parent $flutterBinary
Write-Host "SDK installed: $flutterBinDirectory"
Write-Host 'Run this in the current PowerShell session:'
Write-Host ('$env:Path = ''' + $flutterBinDirectory + ';'' + $env:Path')
Write-Host 'Then run from the project directory: .\setup.ps1 -Device chrome'
