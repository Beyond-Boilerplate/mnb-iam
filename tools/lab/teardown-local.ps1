#Requires -Version 5.1
<#
.SYNOPSIS
  Tear down the Windows IdentityIQ lab created by setup-local.ps1
#>
[CmdletBinding()]
param(
  [switch]$Yes,
  [switch]$KeepAliases,
  [switch]$Help
)

$ErrorActionPreference = "Stop"

function Write-Log([string]$Message) { Write-Host "==> $Message" }
function Die([string]$Message) { Write-Error $Message; exit 1 }

if ($Help) {
  Write-Host @"
IdentityIQ local teardown (Windows)

  .\tools\lab\teardown-local.ps1 -Yes
  .\tools\lab\teardown-local.ps1 -Yes -KeepAliases

Removes Tomcat, lab MySQL, %USERPROFILE%\iiq-lab, %USERPROFILE%\.iiq-lab, and profile aliases.
"@
  exit 0
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StateDir = Join-Path $env:USERPROFILE ".iiq-lab"
$EnvFile = Join-Path $StateDir "env.ps1"
if (Test-Path $EnvFile) { . $EnvFile }

$LabHome = if ($env:IIQ_LAB_HOME) { $env:IIQ_LAB_HOME } else { Join-Path $env:USERPROFILE "iiq-lab" }
$CatalinaHome = if ($env:CATALINA_HOME) { $env:CATALINA_HOME } else { Join-Path $LabHome "tomcat" }
$HttpPort = if ($env:IIQ_HTTP_PORT) { [int]$env:IIQ_HTTP_PORT } else { 8080 }
$DbPort = if ($env:IIQ_DB_PORT) { [int]$env:IIQ_DB_PORT } else { 3307 }

if (-not $Yes) {
  Write-Host @"
This will tear down the IdentityIQ lab:
  Lab home:  $LabHome
  HTTP port: $HttpPort
  DB port:   $DbPort
"@
  $ans = Read-Host "Type 'teardown' to continue"
  if ($ans -ne "teardown") { Die "Aborted" }
}

Write-Log "Stopping Tomcat…"
if (Test-Path (Join-Path $CatalinaHome "bin\shutdown.bat")) {
  & (Join-Path $CatalinaHome "bin\shutdown.bat") 2>$null
  Start-Sleep -Seconds 3
}
try {
  Get-NetTCPConnection -LocalPort $HttpPort -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
} catch {}

Write-Log "Stopping lab MySQL…"
Get-Process mysqld -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
try {
  Get-NetTCPConnection -LocalPort $DbPort -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
} catch {}
Start-Sleep -Seconds 1

Write-Log "Removing $LabHome …"
if (Test-Path $LabHome) { Remove-Item -Recurse -Force $LabHome }

Write-Log "Removing $StateDir …"
if (Test-Path $StateDir) { Remove-Item -Recurse -Force $StateDir }

if (-not $KeepAliases -and (Test-Path $PROFILE)) {
  $marker = "# >>> identityiq-lab aliases >>>"
  $end = "# <<< identityiq-lab aliases <<<"
  $text = Get-Content -Raw $PROFILE
  if ($text.Contains($marker)) {
    $text = [regex]::Replace($text, "(?s)$([regex]::Escape($marker)).*?$([regex]::Escape($end))\r?\n?", "")
    Set-Content -Path $PROFILE -Value $text.TrimEnd() -Encoding UTF8
    Write-Log "Removed aliases from $PROFILE"
  }
}

Write-Host @"

============================================
 IdentityIQ lab teardown complete (Windows)
============================================
 Re-setup:
   .\tools\lab\setup-local.ps1
============================================
"@
