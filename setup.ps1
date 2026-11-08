param(
    [string]$Device
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Command failed with exit code $LASTEXITCODE."
    }
}

Push-Location -LiteralPath $PSScriptRoot
try {
    if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
        throw 'Flutter fehlt. Zuerst .\scripts\install-flutter.ps1 ausfuehren und den angezeigten PATH setzen.'
    }
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw 'Python 3.10+ fehlt. Bitte Python installieren und zum PATH hinzufuegen.'
    }
    Invoke-Checked python @('scripts/bootstrap.py')
    Invoke-Checked flutter @('pub', 'get')
    Invoke-Checked flutter @('analyze')
    Invoke-Checked flutter @('test')
    if ($Device) {
        Invoke-Checked flutter @('run', '-d', $Device)
    } else {
        Write-Host 'Bereit. Starten mit: flutter run -d chrome (oder -d windows).'
    }
} finally {
    Pop-Location
}
