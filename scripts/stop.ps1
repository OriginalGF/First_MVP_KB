param(
  [int]$BackendPort = 8011,
  [int]$FrontendPort = 3001
)

$ErrorActionPreference = "SilentlyContinue"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeDir = Join-Path $scriptDir ".runtime"
$browserProfileDir = Join-Path $runtimeDir "browser-profile"

$backendPidFile = Join-Path $runtimeDir "backend.pid"
$frontendPidFile = Join-Path $runtimeDir "frontend.pid"
$browserPidFile = Join-Path $runtimeDir "browser.pid"

function Stop-FromPidFile {
  param([string]$PidFile)

  if (-not (Test-Path $PidFile)) {
    return
  }

  $pidText = Get-Content $PidFile -ErrorAction SilentlyContinue
  [int]$pidValue = 0
  if ([int]::TryParse(($pidText | Select-Object -First 1), [ref]$pidValue)) {
    $proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($proc) {
      taskkill /PID $pidValue /T /F | Out-Null
      Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
      Write-Output "Stopped PID $pidValue"
    }
  }

  Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

function Stop-ListeningPort {
  param([int]$Port)

  $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  if (-not $connections) {
    return
  }

  $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($pidValue in $pids) {
    Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
    Write-Output "Stopped process on port $Port (PID $pidValue)"
  }
}

function Stop-ManagedBrowserWindows {
  param([string]$ProfileDir)

  if (-not (Test-Path $ProfileDir)) {
    return
  }

  $escapedProfilePath = [regex]::Escape($ProfileDir)
  $browserProcesses = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
      ($_.Name -ieq "chrome.exe" -or $_.Name -ieq "msedge.exe") -and
      $_.CommandLine -and
      $_.CommandLine -match $escapedProfilePath
    }

  foreach ($browserProcess in $browserProcesses) {
    taskkill /PID $browserProcess.ProcessId /T /F | Out-Null
    Stop-Process -Id $browserProcess.ProcessId -Force -ErrorAction SilentlyContinue
    Write-Output "Stopped managed browser PID $($browserProcess.ProcessId)"
  }
}

Stop-FromPidFile -PidFile $browserPidFile
Stop-ManagedBrowserWindows -ProfileDir $browserProfileDir
Stop-FromPidFile -PidFile $frontendPidFile
Stop-FromPidFile -PidFile $backendPidFile

Stop-ListeningPort -Port $FrontendPort
Stop-ListeningPort -Port $BackendPort

Write-Output "Stopped frontend/backend and closed tracked browser process."
