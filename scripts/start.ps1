param(
  [int]$BackendPort = 8011,
  [int]$FrontendPort = 3001,
  [string]$OpenUrl = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = (Resolve-Path (Join-Path $scriptDir "..")).Path
$frontendDir = Join-Path $rootDir "frontend"
$runtimeDir = Join-Path $scriptDir ".runtime"

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

$runId = Get-Date -Format "yyyyMMdd-HHmmss"

$backendPidFile = Join-Path $runtimeDir "backend.pid"
$frontendPidFile = Join-Path $runtimeDir "frontend.pid"
$browserPidFile = Join-Path $runtimeDir "browser.pid"
$backendLogOut = Join-Path $runtimeDir "backend.$runId.out.log"
$backendLogErr = Join-Path $runtimeDir "backend.$runId.err.log"
$frontendLogOut = Join-Path $runtimeDir "frontend.$runId.out.log"
$frontendLogErr = Join-Path $runtimeDir "frontend.$runId.err.log"
$browserProfileDir = Join-Path $runtimeDir "browser-profile"

function Remove-IfRunning {
  param([string]$PidFile)

  if (-not (Test-Path $PidFile)) {
    return
  }

  $pidText = Get-Content $PidFile -ErrorAction SilentlyContinue
  [int]$pidValue = 0
  if ([int]::TryParse(($pidText | Select-Object -First 1), [ref]$pidValue)) {
    $proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($proc) {
      Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
    }
  }

  Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

function Wait-ForHttp {
  param(
    [string]$Url,
    [int]$MaxAttempts = 60,
    [int]$DelayMs = 500
  )

  for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    try {
      $response = Invoke-WebRequest -Uri $Url -TimeoutSec 3 -UseBasicParsing
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
        return $true
      }
    }
    catch {
      Start-Sleep -Milliseconds $DelayMs
    }
  }

  return $false
}

function Wait-ForBackendHealth {
  param(
    [string]$Url,
    [int]$MaxAttempts = 60,
    [int]$DelayMs = 500
  )

  for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    try {
      $payload = Invoke-RestMethod -Uri $Url -TimeoutSec 3
      if ($payload.status -eq "ok" -and $payload.service -eq "project-management-mvp") {
        return $true
      }
    }
    catch {
      Start-Sleep -Milliseconds $DelayMs
    }
  }

  return $false
}

$openTarget = $OpenUrl
if ([string]::IsNullOrWhiteSpace($openTarget)) {
  $openTarget = "http://127.0.0.1:$FrontendPort"
}

# Prevent duplicate stacks from previous runs.
Remove-IfRunning -PidFile $backendPidFile
Remove-IfRunning -PidFile $frontendPidFile
Remove-IfRunning -PidFile $browserPidFile

New-Item -ItemType File -Path $backendLogOut -Force | Out-Null
New-Item -ItemType File -Path $backendLogErr -Force | Out-Null
New-Item -ItemType File -Path $frontendLogOut -Force | Out-Null
New-Item -ItemType File -Path $frontendLogErr -Force | Out-Null

$backendStartArgs = @{
  FilePath = "python"
  ArgumentList = @("-m", "uvicorn", "backend.app.main:app", "--reload", "--host", "127.0.0.1", "--port", "$BackendPort")
  WorkingDirectory = $rootDir
  RedirectStandardOutput = $backendLogOut
  RedirectStandardError = $backendLogErr
  PassThru = $true
}
$backendProc = Start-Process @backendStartArgs

$backendProc.Id | Set-Content $backendPidFile

if (-not (Wait-ForBackendHealth -Url "http://127.0.0.1:$BackendPort/api/health")) {
  throw "Backend failed health check on port $BackendPort. See $backendLogOut and $backendLogErr"
}

$frontendStartArgs = @{
  FilePath = "npm.cmd"
  ArgumentList = @("run", "dev", "--", "--hostname", "127.0.0.1", "--port", "$FrontendPort")
  WorkingDirectory = $frontendDir
  RedirectStandardOutput = $frontendLogOut
  RedirectStandardError = $frontendLogErr
  PassThru = $true
}
$frontendProc = Start-Process @frontendStartArgs

$frontendProc.Id | Set-Content $frontendPidFile

if (-not (Wait-ForHttp -Url "http://127.0.0.1:$FrontendPort")) {
  throw "Frontend failed readiness check on port $FrontendPort. See $frontendLogOut and $frontendLogErr"
}

$browserExe = $null
$chromeCandidates = @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe"
)
$edgeCandidates = @(
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe"
)

foreach ($candidate in ($chromeCandidates + $edgeCandidates)) {
  if (Test-Path $candidate) {
    $browserExe = $candidate
    break
  }
}

if ($browserExe) {
  New-Item -ItemType Directory -Path $browserProfileDir -Force | Out-Null
  $browserStartArgs = @{
    FilePath = $browserExe
    ArgumentList = @("--new-window", "--user-data-dir=$browserProfileDir", $openTarget)
    PassThru = $true
  }
  $browserProc = Start-Process @browserStartArgs

  $browserProc.Id | Set-Content $browserPidFile
}
else {
  Start-Process $openTarget | Out-Null
}

Write-Output "Backend running at http://127.0.0.1:$BackendPort"
Write-Output "Frontend running at http://127.0.0.1:$FrontendPort"
Write-Output "Opened browser to $openTarget"
Write-Output "Logs: $backendLogOut, $backendLogErr, $frontendLogOut, $frontendLogErr"
