# Run after gh auth login. Creates a private repo when origin is absent,
# pushes the current branch, waits for that commit's build, and downloads the IPA.
param(
    [string]$Repository = 'sidestart'
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
    foreach ($requiredCommand in @('git', 'gh')) {
        if (-not (Get-Command $requiredCommand -ErrorAction SilentlyContinue)) {
            throw "Missing command: $requiredCommand"
        }
    }
    & gh auth status
    if ($LASTEXITCODE -ne 0) {
        throw 'GitHub authentication is missing or expired. Run gh auth login first.'
    }
    if (-not (Test-Path -LiteralPath '.git')) {
        Invoke-Checked git @('init', '-b', 'main')
        Invoke-Checked git @('add', '.')
        Invoke-Checked git @('commit', '-m', 'Initial SideStart Flutter app and sideload builds')
    }
    $pendingChanges = & git status --porcelain
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read git status.' }
    if ($pendingChanges) {
        throw 'Uncommitted changes. Review them and git add / git commit before publishing.'
    }
    $branch = (& git branch --show-current).Trim()
    if ($branch -notin @('main', 'master')) {
        throw 'Publish main or master so that the push workflow runs.'
    }
    $commit = (& git rev-parse HEAD).Trim()
    $remoteNames = @(& git remote)
    if ($remoteNames -notcontains 'origin') {
        Invoke-Checked gh @('repo', 'create', $Repository, '--private', '--source', '.', '--remote', 'origin', '--push')
    } else {
        Invoke-Checked git @('push', '-u', 'origin', $branch)
    }

    Write-Host "Waiting for the build of $commit ..."
    $buildRun = $null
    for ($attempt = 0; $attempt -lt 24; $attempt++) {
        $runJson = & gh run list --workflow builds.yml --branch $branch --commit $commit --event push --limit 1 --json databaseId
        if ($LASTEXITCODE -eq 0) {
            $runs = @(ConvertFrom-Json -InputObject ($runJson -join "`n") | ForEach-Object { $_ })
            if ($runs.Count -gt 0) {
                $buildRun = $runs[0].databaseId
                break
            }
        }
        Start-Sleep -Seconds 5
    }
    if (-not $buildRun) {
        throw 'No push build found. Check GitHub Actions permissions and gh run list --workflow builds.yml.'
    }
    & gh run watch "$buildRun" --exit-status
    if ($LASTEXITCODE -ne 0) {
        Write-Host "GitHub build $buildRun failed. Job error log:"
        & gh run view "$buildRun" --log-failed
        throw "Build $buildRun failed. The job log above contains the actual build error."
    }
    $downloadDirectory = Join-Path $PSScriptRoot "downloads\run-$buildRun"
    Invoke-Checked gh @('run', 'download', "$buildRun", '--name', 'sidestart-ios-unsigned', '--dir', $downloadDirectory)
    Write-Host "IPA and checksum: $downloadDirectory"
    Write-Host 'Transfer the IPA to your iPhone and import it with SideStore.'
} finally {
    Pop-Location
}
