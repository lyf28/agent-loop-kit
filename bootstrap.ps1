param(
    [string]$HarnessUrl
)

$ErrorActionPreference = "Stop"

function Assert-CommandAvailable {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required for the Windows MVP. $InstallHint"
    }
}

function Convert-ToSingleQuotedPowerShellString {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    return "'" + ($Value -replace "'", "''") + "'"
}

Assert-CommandAvailable -Name "python" -InstallHint "Install Python and make sure python is available on PATH, then re-run .\bootstrap.ps1."
Assert-CommandAvailable -Name "codex" -InstallHint "Install the Codex CLI and make sure codex is available on PATH, then re-run .\bootstrap.ps1."
Assert-CommandAvailable -Name "gh" -InstallHint "Install GitHub CLI and make sure gh is available on PATH, then re-run .\bootstrap.ps1."

& gh auth status *> $null

if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run gh auth login from PowerShell, then re-run .\bootstrap.ps1."
}

$kitRoot = $PSScriptRoot

if (-not $kitRoot) {
    $kitRoot = (Get-Location).Path
}

$loopPath = Join-Path $kitRoot "loopkit\loop.py"

if (-not (Test-Path -LiteralPath $loopPath)) {
    throw "Could not find loop runner at $loopPath"
}

if (-not $HarnessUrl) {
    try {
        $HarnessUrl = (& git -C $kitRoot remote get-url origin 2>$null).Trim()
    }
    catch {
        $HarnessUrl = ""
    }
}

if (-not $HarnessUrl) {
    throw "Could not detect harness URL from git remote. Re-run with -HarnessUrl https://github.com/user/repo"
}

$binDir = Join-Path $env:USERPROFILE ".agent-loop\bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null

$psShimPath = Join-Path $binDir "agent-loop.ps1"
$cmdShimPath = Join-Path $binDir "agent-loop.cmd"

$quotedLoopPath = Convert-ToSingleQuotedPowerShellString -Value $loopPath
$quotedHarnessUrl = Convert-ToSingleQuotedPowerShellString -Value $HarnessUrl

$psShim = @"
`$ErrorActionPreference = "Stop"

`$LoopPath = $quotedLoopPath
`$HarnessUrl = $quotedHarnessUrl
`$TaskParts = @(`$args)

if (`$TaskParts.Count -eq 0) {
    Write-Error 'Usage: agent-loop "your task"'
    exit 64
}

`$Task = `$TaskParts -join ' '

& python `$LoopPath `$HarnessUrl `$Task
exit `$LASTEXITCODE
"@

Set-Content -LiteralPath $psShimPath -Value $psShim -Encoding UTF8

$cmdShim = @"
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0agent-loop.ps1" %*
exit /b %ERRORLEVEL%
"@

Set-Content -LiteralPath $cmdShimPath -Value $cmdShim -Encoding ASCII

$currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")

if (-not $currentUserPath) {
    $currentUserPath = ""
}

$pathEntries = $currentUserPath -split ";" |
    Where-Object { $_ } |
    ForEach-Object { $_.TrimEnd("\") }

$normalizedBinDir = $binDir.TrimEnd("\")
$pathContainsBinDir = $pathEntries |
    Where-Object { $_ -ieq $normalizedBinDir } |
    Select-Object -First 1

if (-not $pathContainsBinDir) {
    if ($currentUserPath.Trim()) {
        $newUserPath = $currentUserPath.TrimEnd(";") + ";" + $binDir
    }
    else {
        $newUserPath = $binDir
    }

    [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
    $pathUpdated = $true
}
else {
    $pathUpdated = $false
}

$currentProcessPath = $env:Path

if (-not $currentProcessPath) {
    $currentProcessPath = ""
}

$processPathEntries = $currentProcessPath -split ";" |
    Where-Object { $_ } |
    ForEach-Object { $_.TrimEnd("\") }

$processPathContainsBinDir = $processPathEntries |
    Where-Object { $_ -ieq $normalizedBinDir } |
    Select-Object -First 1

if (-not $processPathContainsBinDir) {
    if ($currentProcessPath.Trim()) {
        $env:Path = $currentProcessPath.TrimEnd(";") + ";" + $binDir
    }
    else {
        $env:Path = $binDir
    }

    $processPathUpdated = $true
}
else {
    $processPathUpdated = $false
}

Write-Host "Installed agent-loop shims:"
Write-Host "  $psShimPath"
Write-Host "  $cmdShimPath"
Write-Host ""
Write-Host "Harness URL:"
Write-Host "  $HarnessUrl"
Write-Host ""

if ($pathUpdated) {
    Write-Host "Added to your user PATH:"
    Write-Host "  $binDir"
    Write-Host ""
}
else {
    Write-Host "Your user PATH already includes:"
    Write-Host "  $binDir"
    Write-Host ""
}

if ($processPathUpdated) {
    Write-Host "Added to this PowerShell session PATH."
}
else {
    Write-Host "This PowerShell session PATH already includes:"
    Write-Host "  $binDir"
}

Write-Host ""
Write-Host "Run now:"
Write-Host '  agent-loop "your task"'
Write-Host ""
Write-Host "Direct shim fallback:"
Write-Host "  & `"$psShimPath`" `"your task`""
