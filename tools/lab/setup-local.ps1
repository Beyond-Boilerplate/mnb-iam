#Requires -Version 5.1
<#
.SYNOPSIS
  Greenfield IdentityIQ 8.5 lab setup for Windows (PowerShell).

.DESCRIPTION
  On a brand-new Windows machine this script will:
    - Ensure curl / tar / winget where possible
    - Install or download Temurin JDK 11
    - Download portable MySQL 8.4 into %USERPROFILE%\iiq-lab\mysql
    - Download Apache Tomcat 9 into %USERPROFILE%\iiq-lab\tomcat
    - Deploy identityiq.war, configure iiq.properties, import init.xml (+ LCM)
    - Start Tomcat and wait for the login page

  Git Bash users: run this script instead of setup-local.sh

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\tools\lab\setup-local.ps1
  .\tools\lab\setup-local.ps1 -ForceDb
  .\tools\lab\setup-local.ps1 -Check
#>
[CmdletBinding()]
param(
  [switch]$SkipImport,
  [switch]$NoStart,
  [switch]$ForceDb,
  [switch]$Check,
  [switch]$Help
)

$ErrorActionPreference = "Stop"

function Write-Log([string]$Message) { Write-Host "==> $Message" }
function Write-Warn([string]$Message) { Write-Warning $Message }
function Die([string]$Message) { Write-Error $Message; exit 1 }

if ($Help) {
  Write-Host @"
IdentityIQ local setup (Windows PowerShell)

Options:
  -SkipImport   Skip init.xml / init-lcm.xml import
  -NoStart      Do not start Tomcat
  -ForceDb      Recreate IdentityIQ schemas
  -Check        Preflight only
  -Help         Show help

macOS / Linux / WSL: ./tools/lab/setup-local.sh
"@
  exit 0
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$WarPath = Join-Path $RepoRoot "base\ga\identityiq-8.5.zip"
$SqlCreate = Join-Path $RepoRoot "docs\vendor\iiq-8.5\database\create_identityiq_tables-8.5.mysql"

$LabHome = if ($env:IIQ_LAB_HOME) { $env:IIQ_LAB_HOME } else { Join-Path $env:USERPROFILE "iiq-lab" }
$StateDir = if ($env:IIQ_LAB_STATE_DIR) { $env:IIQ_LAB_STATE_DIR } else { Join-Path $env:USERPROFILE ".iiq-lab" }
$EnvFile = Join-Path $StateDir "env.ps1"
$LogDir = Join-Path $StateDir "logs"
$CatalinaHome = Join-Path $LabHome "tomcat"
$IiqHome = Join-Path $CatalinaHome "webapps\identityiq"
$LabData = Join-Path $LabHome "data"
$HttpPort = if ($env:IIQ_HTTP_PORT) { [int]$env:IIQ_HTTP_PORT } else { 8080 }
$DbPort = if ($env:IIQ_DB_PORT) { [int]$env:IIQ_DB_PORT } else { 3307 }
$TomcatVersion = if ($env:IIQ_TOMCAT_VERSION) { $env:IIQ_TOMCAT_VERSION } else { "9.0.120" }
$MysqlVersion = "8.4.5"

New-Item -ItemType Directory -Force -Path $LabHome, $StateDir, $LogDir, $LabData | Out-Null

function Test-Command($Name) { return [bool](Get-Command $Name -ErrorAction SilentlyContinue) }

function Test-PortInUse([int]$Port) {
  try {
    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $listeners
  } catch {
    # Fallback for older Windows without Get-NetTCPConnection permissions
    $out = netstat -ano | Select-String ":$Port\s+.*LISTENING"
    return $null -ne $out
  }
}

function Invoke-Download([string]$Url, [string]$Dest) {
  Write-Log "Downloading $(Split-Path $Dest -Leaf)…"
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  Invoke-WebRequest -Uri $Url -OutFile $Dest -UseBasicParsing
}

if ($Check) {
  Write-Host "Platform: Windows"
  Write-Host "Repo:     $RepoRoot"
  Write-Host "WAR:      $(if (Test-Path $WarPath) { 'OK' } else { 'MISSING' })"
  Write-Host "winget:   $(if (Test-Command winget) { 'OK' } else { 'missing' })"
  Write-Host "java:     $(if (Test-Command java) { (java -version 2>&1 | Select-Object -First 1) } else { 'missing' })"
  Write-Host "Tip: run without -Check to bootstrap + install."
  exit 0
}

if (-not (Test-Path $WarPath)) { Die "Missing WAR: $WarPath" }
if (-not (Test-Path $SqlCreate)) { Die "Missing SQL: $SqlCreate" }

$SetupLog = Join-Path $LogDir ("setup-{0:yyyyMMdd-HHmmss}.log" -f (Get-Date))
Start-Transcript -Path $SetupLog -Append | Out-Null
Write-Log "SailPoint root: $RepoRoot"
Write-Log "Lab home:       $LabHome"
Write-Log "Setup log:      $SetupLog"

# ---------------------------------------------------------------------------
# JDK 11
# ---------------------------------------------------------------------------
function Resolve-JavaHome {
  $candidates = @()
  if ($env:JAVA_HOME -and (Test-Path (Join-Path $env:JAVA_HOME "bin\java.exe"))) {
    $candidates += $env:JAVA_HOME
  }
  $portable = Join-Path $LabHome "jdk"
  if (Test-Path (Join-Path $portable "bin\java.exe")) { $candidates += $portable }
  $candidates += @(
    "C:\Program Files\Eclipse Adoptium\jdk-11*",
    "C:\Program Files\Microsoft\jdk-11*",
    "C:\Program Files\Java\jdk-11*"
  ) | ForEach-Object { Get-Item $_ -ErrorAction SilentlyContinue } | ForEach-Object { $_.FullName }

  foreach ($c in $candidates) {
    $java = Join-Path $c "bin\java.exe"
    if (Test-Path $java) {
      $ver = & $java -version 2>&1 | Select-Object -First 1 | Out-String
      if ($ver -match 'version "(1\.)?(\d+)') {
        $major = [int]$Matches[2]
        if ($major -ge 11 -and $major -le 17) {
          return $c
        }
      }
    }
  }
  return $null
}

$JavaHome = Resolve-JavaHome
if (-not $JavaHome) {
  Write-Log "No JDK 11/17 found — installing…"
  if (Test-Command winget) {
    try {
      winget install --id EclipseAdoptium.Temurin.11.JDK -e --accept-package-agreements --accept-source-agreements
    } catch {
      Write-Warn "winget Temurin install failed; falling back to portable ZIP"
    }
    $JavaHome = Resolve-JavaHome
  }
  if (-not $JavaHome) {
    $arch = if ([Environment]::Is64BitOperatingSystem) {
      if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "aarch64" } else { "x64" }
    } else { Die "32-bit Windows is not supported" }
    $jdkZip = Join-Path $LabHome "temurin11.zip"
    $url = "https://api.adoptium.net/v3/binary/latest/11/ga/windows/$arch/jdk/hotspot/normal/eclipse?project=jdk"
    Invoke-Download $url $jdkZip
    $jdkDir = Join-Path $LabHome "jdk"
    if (Test-Path $jdkDir) { Remove-Item -Recurse -Force $jdkDir }
    Expand-Archive -Path $jdkZip -DestinationPath (Join-Path $LabHome "jdk-extract") -Force
    $extracted = Get-ChildItem (Join-Path $LabHome "jdk-extract") -Directory | Select-Object -First 1
    Move-Item $extracted.FullName $jdkDir
    Remove-Item -Recurse -Force (Join-Path $LabHome "jdk-extract"), $jdkZip
    $JavaHome = $jdkDir
  }
}
if (-not $JavaHome) { Die "Failed to install JDK 11" }
$env:JAVA_HOME = $JavaHome
$env:Path = "$JavaHome\bin;" + $env:Path
Write-Log "Using JAVA_HOME=$JavaHome"

# ---------------------------------------------------------------------------
# MySQL portable (lab port)
# ---------------------------------------------------------------------------
$MysqlDist = Join-Path $LabHome "mysql\dist"
$MysqlData = Join-Path $LabHome "mysql\data"
$MysqlBin = Join-Path $MysqlDist "bin"
$Mysqld = Join-Path $MysqlBin "mysqld.exe"
$MysqlExe = Join-Path $MysqlBin "mysql.exe"

function Ensure-Mysql {
  if (-not (Test-Path $Mysqld)) {
    Write-Log "Downloading portable MySQL $MysqlVersion…"
    $archTag = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "winx64" } else { "winx64" } # Oracle ships winx64 primarily
    $zipName = "mysql-$MysqlVersion-$archTag.zip"
    $url = "https://cdn.mysql.com/archives/mysql-8.4/$zipName"
    $zipPath = Join-Path $LabHome "mysql\$zipName"
    New-Item -ItemType Directory -Force -Path (Join-Path $LabHome "mysql") | Out-Null
    try {
      Invoke-Download $url $zipPath
    } catch {
      Die @"
Failed to download MySQL from $url

Install MySQL 8.4 manually, or on a fresh PC ensure outbound HTTPS works, then re-run.
Alternative: use WSL2 and ./tools/lab/setup-local.sh
"@
    }
    Expand-Archive -Path $zipPath -DestinationPath (Join-Path $LabHome "mysql\extract") -Force
    $extracted = Get-ChildItem (Join-Path $LabHome "mysql\extract") -Directory | Select-Object -First 1
    if (Test-Path $MysqlDist) { Remove-Item -Recurse -Force $MysqlDist }
    Move-Item $extracted.FullName $MysqlDist
    Remove-Item -Recurse -Force (Join-Path $LabHome "mysql\extract"), $zipPath
  }
  if (-not (Test-Path $Mysqld)) { Die "mysqld.exe missing at $Mysqld" }

  if ($ForceDb -and (Test-Path $MysqlData)) {
    Write-Log "ForceDb: removing MySQL datadir…"
    # Stop first if running
    Get-Process mysqld -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Remove-Item -Recurse -Force $MysqlData
  }

  if (-not (Test-Path (Join-Path $MysqlData "mysql"))) {
    Write-Log "Initializing MySQL datadir…"
    New-Item -ItemType Directory -Force -Path $MysqlData | Out-Null
    & $Mysqld --initialize-insecure --datadir=$MysqlData --basedir=$MysqlDist
  }

  # Start if not accepting connections
  $env:Path = "$MysqlBin;" + $env:Path
  $ok = $false
  try {
    & $MysqlExe -h 127.0.0.1 -P $DbPort -u root -e "SELECT 1" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $ok = $true }
  } catch { $ok = $false }

  if (-not $ok) {
    if (Test-PortInUse $DbPort) {
      foreach ($alt in 3307, 3308, 3309, 3310) {
        if (-not (Test-PortInUse $alt)) { $script:DbPort = $alt; $DbPort = $alt; break }
      }
    }
    Write-Log "Starting lab MySQL on 127.0.0.1:$DbPort…"
    $errLog = Join-Path $LabHome "mysql\mysqld.err"
    Start-Process -FilePath $Mysqld -ArgumentList @(
      "--datadir=$MysqlData",
      "--basedir=$MysqlDist",
      "--port=$DbPort",
      "--bind-address=127.0.0.1",
      "--mysqlx=0"
    ) -WindowStyle Hidden -RedirectStandardError $errLog
    $deadline = (Get-Date).AddMinutes(2)
    do {
      Start-Sleep -Seconds 2
      try {
        & $MysqlExe -h 127.0.0.1 -P $DbPort -u root -e "SELECT 1" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $ok = $true; break }
      } catch {}
    } while ((Get-Date) -lt $deadline)
    if (-not $ok) {
      if (Test-Path $errLog) { Get-Content $errLog -Tail 40 }
      Die "Lab MySQL did not become ready on port $DbPort"
    }
  }
  Write-Log "MySQL ready on port $DbPort"
}

Ensure-Mysql

function Invoke-MysqlRoot([string]$Sql) {
  & $MysqlExe -h 127.0.0.1 -P $DbPort -u root -e $Sql
  if ($LASTEXITCODE -ne 0) { Die "MySQL command failed: $Sql" }
}

function Invoke-MysqlRootFile([string]$Path) {
  Get-Content -Raw $Path | & $MysqlExe -h 127.0.0.1 -P $DbPort -u root
  if ($LASTEXITCODE -ne 0) { Die "MySQL import failed: $Path" }
}

# Create schemas
$exists = & $MysqlExe -h 127.0.0.1 -P $DbPort -u root -N -e "SHOW DATABASES LIKE 'identityiq';" 2>$null
if ($ForceDb -or -not $exists) {
  if ($ForceDb) {
    Write-Log "Dropping existing IIQ schemas…"
    Invoke-MysqlRoot "DROP DATABASE IF EXISTS identityiq; DROP DATABASE IF EXISTS identityiqah; DROP DATABASE IF EXISTS identityiqPlugin;"
  }
  Write-Log "Creating IdentityIQ schemas…"
  $tmpSql = Join-Path $env:TEMP "iiq-create.sql"
  (Get-Content -Raw $SqlCreate) -replace 'IDENTIFIED WITH mysql_native_password BY', 'IDENTIFIED WITH caching_sha2_password BY' |
    Set-Content -Path $tmpSql -Encoding UTF8
  Invoke-MysqlRootFile $tmpSql
  Remove-Item $tmpSql -Force
}
Invoke-MysqlRoot @"
CREATE USER IF NOT EXISTS 'identityiq'@'127.0.0.1' IDENTIFIED WITH caching_sha2_password BY 'identityiq';
GRANT ALL PRIVILEGES ON identityiq.* TO 'identityiq'@'127.0.0.1';
CREATE USER IF NOT EXISTS 'identityiqah'@'127.0.0.1' IDENTIFIED WITH caching_sha2_password BY 'identityiqah';
GRANT ALL PRIVILEGES ON identityiqah.* TO 'identityiqah'@'127.0.0.1';
CREATE USER IF NOT EXISTS 'identityiqPlugin'@'127.0.0.1' IDENTIFIED WITH caching_sha2_password BY 'identityiqPlugin';
GRANT ALL PRIVILEGES ON identityiqPlugin.* TO 'identityiqPlugin'@'127.0.0.1';
FLUSH PRIVILEGES;
"@

# ---------------------------------------------------------------------------
# Tomcat
# ---------------------------------------------------------------------------
if (-not (Test-Path (Join-Path $CatalinaHome "bin\catalina.bat"))) {
  Write-Log "Downloading Apache Tomcat $TomcatVersion…"
  $tgz = Join-Path $LabHome "tomcat.tgz"
  $url = "https://dlcdn.apache.org/tomcat/tomcat-9/v$TomcatVersion/bin/apache-tomcat-$TomcatVersion-windows-x64.zip"
  $zip = Join-Path $LabHome "tomcat.zip"
  try {
    Invoke-Download $url $zip
  } catch {
    $url = "https://archive.apache.org/dist/tomcat/tomcat-9/v$TomcatVersion/bin/apache-tomcat-$TomcatVersion-windows-x64.zip"
    Invoke-Download $url $zip
  }
  Expand-Archive -Path $zip -DestinationPath (Join-Path $LabHome "tomcat-extract") -Force
  $extracted = Get-ChildItem (Join-Path $LabHome "tomcat-extract") -Directory | Select-Object -First 1
  if (Test-Path $CatalinaHome) { Remove-Item -Recurse -Force $CatalinaHome }
  Move-Item $extracted.FullName $CatalinaHome
  Remove-Item -Recurse -Force (Join-Path $LabHome "tomcat-extract"), $zip
}

# setenv.bat
$setenv = Join-Path $CatalinaHome "bin\setenv.bat"
@"
set `"JAVA_HOME=$JavaHome`"
set `"JAVA_OPTS=-Xms1024m -Xmx2048m -Djava.awt.headless=true -Dfile.encoding=UTF-8`"
"@ | Set-Content -Path $setenv -Encoding ASCII

# Deploy WAR
Write-Log "Deploying identityiq.war…"
if (Test-PortInUse $HttpPort) {
  Write-Log "Stopping process on :$HttpPort…"
  & (Join-Path $CatalinaHome "bin\shutdown.bat") 2>$null
  Start-Sleep -Seconds 3
  Get-NetTCPConnection -LocalPort $HttpPort -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
if (Test-Path $IiqHome) { Remove-Item -Recurse -Force $IiqHome }
New-Item -ItemType Directory -Force -Path $IiqHome | Out-Null
Push-Location $IiqHome
& jar xf $WarPath
Pop-Location

# iiq.properties
$props = Join-Path $IiqHome "WEB-INF\classes\iiq.properties"
Copy-Item $props "$props.bak" -Force
function Set-Prop([string]$Text, [string]$Key, [string]$Value) {
  $pattern = "(?m)^(\s*#\s*)?$([regex]::Escape($Key))=.*$"
  if ($Text -match $pattern) {
    return [regex]::Replace($Text, $pattern, "$Key=$Value", 1)
  }
  return $Text + "`r`n$Key=$Value`r`n"
}
function Mysql-Url([string]$Db) {
  return "jdbc:mysql://127.0.0.1:$DbPort/$Db?useServerPrepStmts=true&tinyInt1isBit=true&useSSL=false&characterEncoding=UTF-8&serverTimezone=UTC&allowPublicKeyRetrieval=true"
}
$p = Get-Content -Raw $props
$p = Set-Prop $p "dataSource.username" "identityiq"
$p = Set-Prop $p "dataSource.password" "identityiq"
$p = Set-Prop $p "dataSource.url" (Mysql-Url "identityiq")
$p = Set-Prop $p "dataSource.driverClassName" "com.mysql.cj.jdbc.Driver"
$p = Set-Prop $p "pluginsDataSource.username" "identityiqPlugin"
$p = Set-Prop $p "pluginsDataSource.password" "identityiqPlugin"
$p = Set-Prop $p "pluginsDataSource.url" (Mysql-Url "identityiqPlugin")
$p = Set-Prop $p "pluginsDataSource.driverClassName" "com.mysql.cj.jdbc.Driver"
$p = Set-Prop $p "dataSourceAccessHistory.username" "identityiqah"
$p = Set-Prop $p "dataSourceAccessHistory.password" "identityiqah"
$p = Set-Prop $p "dataSourceAccessHistory.url" (Mysql-Url "identityiqah")
$p = Set-Prop $p "dataSourceAccessHistory.driverClassName" "com.mysql.cj.jdbc.Driver"
Set-Content -Path $props -Value $p -Encoding UTF8
Write-Log "Configured iiq.properties"

# Import init
if (-not $SkipImport) {
  $count = & $MysqlExe -h 127.0.0.1 -P $DbPort -u root -N -e "SELECT COUNT(*) FROM identityiq.spt_identity WHERE name='spadmin';" 2>$null
  if ($ForceDb -or $count -eq "0" -or -not $count) {
    Write-Log "Importing init.xml (several minutes)…"
    $iiqBat = Join-Path $IiqHome "WEB-INF\bin\iiq.bat"
    $env:SPHOME = $IiqHome
    Push-Location (Join-Path $IiqHome "WEB-INF\bin")
    "import init.xml`r`nquit`r`n" | & .\iiq.bat console
    "import init-lcm.xml`r`nquit`r`n" | & .\iiq.bat console
    Pop-Location
  } else {
    Write-Log "spadmin already present — skipping import (use -ForceDb to rebuild)"
  }
}

# Lab data
foreach ($f in @("HRApplications.txt", "EmployeeData.txt", "email.txt")) {
  $src = Join-Path $RepoRoot $f
  if (Test-Path $src) { Copy-Item $src $LabData -Force }
}

# Persist env
@"
# IdentityIQ lab env (Windows)
`$env:SAILPOINT_ROOT = '$RepoRoot'
`$env:IIQ_LAB_HOME = '$LabHome'
`$env:IIQ_LAB_DATA = '$LabData'
`$env:CATALINA_HOME = '$CatalinaHome'
`$env:IIQ_HOME = '$IiqHome'
`$env:JAVA_HOME = '$JavaHome'
`$env:IIQ_HTTP_PORT = '$HttpPort'
`$env:IIQ_DB_PORT = '$DbPort'
`$env:IIQ_URL = 'http://localhost:$HttpPort/identityiq'
`$env:IIQ_MYSQL_BIN = '$MysqlBin'
`$env:Path = "`$env:JAVA_HOME\bin;`$env:CATALINA_HOME\bin;`$env:IIQ_MYSQL_BIN;" + `$env:Path
"@ | Set-Content -Path $EnvFile -Encoding UTF8

# Profile snippet
$profileDir = Split-Path $PROFILE -Parent
if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Force -Path $profileDir | Out-Null }
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE | Out-Null }
$marker = "# >>> identityiq-lab aliases >>>"
$end = "# <<< identityiq-lab aliases <<<"
$profileText = Get-Content -Raw $PROFILE -ErrorAction SilentlyContinue
if ($profileText -and $profileText.Contains($marker)) {
  $profileText = [regex]::Replace($profileText, "(?s)$([regex]::Escape($marker)).*?$([regex]::Escape($end))", "").TrimEnd()
  Set-Content -Path $PROFILE -Value $profileText -Encoding UTF8
}
Add-Content -Path $PROFILE -Encoding UTF8 -Value @"

$marker
# IdentityIQ lab — managed by setup-local.ps1
. '$EnvFile'
. '$ScriptDir\iiq-aliases.ps1'
$end
"@
Write-Log "Aliases wired into PowerShell profile: $PROFILE"

# Start Tomcat
if (-not $NoStart) {
  Write-Log "Starting Tomcat…"
  $env:CATALINA_HOME = $CatalinaHome
  Start-Process -FilePath (Join-Path $CatalinaHome "bin\startup.bat") -WorkingDirectory (Join-Path $CatalinaHome "bin")
  $login = "http://localhost:$HttpPort/identityiq/login.jsf"
  Write-Log "Waiting for $login …"
  $ok = $false
  for ($i = 0; $i -lt 150; $i++) {
    try {
      $r = Invoke-WebRequest -Uri $login -UseBasicParsing -TimeoutSec 3
      if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 2 }
  }
  if (-not $ok) {
    $log = Join-Path $CatalinaHome "logs\catalina.*.log"
    Get-ChildItem $log -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending |
      Select-Object -First 1 | Get-Content -Tail 40
    Die "Timed out waiting for IdentityIQ login page"
  }
  Write-Log "IdentityIQ is up"
}

Stop-Transcript | Out-Null

Write-Host @"

============================================
 IdentityIQ lab setup complete (Windows)
============================================
 URL:      http://localhost:$HttpPort/identityiq
 User:     spadmin
 Password: admin
 IIQ home: $IiqHome
 Lab data: $LabData
 Env file: $EnvFile

 Reload aliases:
   . `$PROFILE
   iiq-help

 Teardown:
   .\tools\lab\teardown-local.ps1 -Yes
============================================
"@
