# IdentityIQ lab aliases for Windows PowerShell
# Sourced from $PROFILE by setup-local.ps1

function _iiq_lab_load {
  $envFile = if ($env:IIQ_LAB_ENV_FILE) { $env:IIQ_LAB_ENV_FILE } else { Join-Path $env:USERPROFILE ".iiq-lab\env.ps1" }
  if (Test-Path $envFile) { . $envFile }
}

function iiq-env {
  _iiq_lab_load
  "SAILPOINT_ROOT=$env:SAILPOINT_ROOT"
  "IIQ_LAB_HOME=$env:IIQ_LAB_HOME"
  "CATALINA_HOME=$env:CATALINA_HOME"
  "IIQ_HOME=$env:IIQ_HOME"
  "JAVA_HOME=$env:JAVA_HOME"
  "IIQ_URL=$env:IIQ_URL"
  "IIQ_LAB_DATA=$env:IIQ_LAB_DATA"
}

function iiq-status {
  _iiq_lab_load
  $port = if ($env:IIQ_HTTP_PORT) { $env:IIQ_HTTP_PORT } else { 8080 }
  $dbport = if ($env:IIQ_DB_PORT) { $env:IIQ_DB_PORT } else { 3307 }
  Write-Host "--- Java ---"
  if ($env:JAVA_HOME) { & "$env:JAVA_HOME\bin\java.exe" -version 2>&1 | Select-Object -First 1 } else { "java missing" }
  Write-Host "--- Tomcat :$port ---"
  try {
    $l = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($l) { "LISTEN: yes" } else { "LISTEN: no" }
  } catch { "LISTEN: unknown" }
  Write-Host "--- MySQL :$dbport ---"
  try {
    $l = Get-NetTCPConnection -LocalPort $dbport -State Listen -ErrorAction SilentlyContinue
    if ($l) { "LISTEN: yes" } else { "LISTEN: no" }
  } catch { "LISTEN: unknown" }
  Write-Host "--- HTTP ---"
  $url = if ($env:IIQ_URL) { "$($env:IIQ_URL)/login.jsf" } else { "http://localhost:$port/identityiq/login.jsf" }
  try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3
    "IdentityIQ login page: UP ($url) [$($r.StatusCode)]"
  } catch {
    "IdentityIQ login page: DOWN ($url)"
  }
}

function iiq-start {
  _iiq_lab_load
  if (-not $env:CATALINA_HOME) { Write-Error "CATALINA_HOME missing. Run setup-local.ps1 first."; return }
  Start-Process -FilePath "$env:CATALINA_HOME\bin\startup.bat" -WorkingDirectory "$env:CATALINA_HOME\bin"
  "Starting… try iiq-status"
}

function iiq-stop {
  _iiq_lab_load
  if ($env:CATALINA_HOME -and (Test-Path "$env:CATALINA_HOME\bin\shutdown.bat")) {
    & "$env:CATALINA_HOME\bin\shutdown.bat"
  }
  $port = if ($env:IIQ_HTTP_PORT) { [int]$env:IIQ_HTTP_PORT } else { 8080 }
  Start-Sleep -Seconds 2
  try {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
      ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
  } catch {}
  "Stopped."
}

function iiq-restart { iiq-stop; Start-Sleep -Seconds 2; iiq-start }

function iiq-logs {
  _iiq_lab_load
  $logs = Get-ChildItem "$env:CATALINA_HOME\logs\catalina*.log" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $logs) { Write-Error "No catalina log found"; return }
  Get-Content $logs.FullName -Wait -Tail 100
}

function iiq-console {
  _iiq_lab_load
  $env:SPHOME = $env:IIQ_HOME
  Push-Location "$env:IIQ_HOME\WEB-INF\bin"
  & .\iiq.bat console @args
  Pop-Location
}

function iiq-open {
  _iiq_lab_load
  $url = if ($env:IIQ_URL) { $env:IIQ_URL } else { "http://localhost:8080/identityiq" }
  Start-Process $url
}

function iiq-mysql-start {
  _iiq_lab_load
  $mysqld = Join-Path $env:IIQ_MYSQL_BIN "mysqld.exe"
  $dist = Split-Path (Split-Path $env:IIQ_MYSQL_BIN -Parent) -Parent
  # IIQ_MYSQL_BIN is ...\mysql\dist\bin → basedir is ...\mysql\dist
  $basedir = Split-Path $env:IIQ_MYSQL_BIN -Parent
  $datadir = Join-Path $env:IIQ_LAB_HOME "mysql\data"
  $port = if ($env:IIQ_DB_PORT) { $env:IIQ_DB_PORT } else { 3307 }
  Start-Process -FilePath $mysqld -ArgumentList @(
    "--datadir=$datadir", "--basedir=$basedir", "--port=$port",
    "--bind-address=127.0.0.1", "--mysqlx=0"
  ) -WindowStyle Hidden
  "Started lab MySQL on :$port"
}

function iiq-mysql-stop {
  Get-Process mysqld -ErrorAction SilentlyContinue | Stop-Process -Force
  "Stopped mysqld"
}

function iiq-help {
  @"
IdentityIQ lab aliases (Windows)

  iiq-env          Show lab paths / URL
  iiq-status       Smoke check
  iiq-start        Start Tomcat
  iiq-stop         Stop Tomcat
  iiq-restart      Restart Tomcat
  iiq-mysql-start  Start lab MySQL
  iiq-mysql-stop   Stop lab MySQL
  iiq-logs         Tail catalina log
  iiq-console      IdentityIQ console
  iiq-open         Open IIQ in browser
  iiq-help         This help

Setup / teardown:
  .\tools\lab\setup-local.ps1
  .\tools\lab\teardown-local.ps1 -Yes
"@
}

_iiq_lab_load
if ($env:IIQ_LAB_HOME) {
  Write-Host "IdentityIQ lab aliases loaded. Try: iiq-help"
}
