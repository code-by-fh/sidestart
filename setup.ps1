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
        throw 'Flutter is missing. Run .\scripts\install-flutter.ps1 first and apply the displayed PATH command.'
    }
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw 'Python 3.10+ is missing. Install Python and add it to PATH.'
    }
    Invoke-Checked python @('scripts/bootstrap.py')
    Invoke-Checked flutter @('pub', 'get')
    Invoke-Checked flutter @('analyze')
    Invoke-Checked flutter @('test')
    if ($Device) {
        Invoke-Checked flutter @('run', '-d', $Device)
    } else {
        Write-Host 'Ready. Start with: flutter run -d chrome (or -d windows).'
    }
} finally {
    Pop-Location
}
