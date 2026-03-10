Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $projectRoot

Write-Host "[GDP MVP Smoke] project root: $projectRoot"

# Basic syntax sanity for simplified critical files.
python -m py_compile `
  src/alias/agent/run.py `
  src/alias/server/schemas/chat.py `
  src/alias/server/alembic/versions/20251125_1130_b8e52f791852_init.py
Write-Host "[GDP MVP Smoke] py_compile passed"

# Try installed entry points first, then fallback to module mode.
function Try-Command {
  param(
    [string]$Name,
    [string[]]$Args
  )
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if ($cmd) {
    & $Name @Args
    return $true
  }
  return $false
}

$entryChecked = $false
if (Try-Command -Name "gdp_agent" -Args @("--help")) {
  Write-Host "[GDP MVP Smoke] gdp_agent --help passed"
  $entryChecked = $true
}
if (Try-Command -Name "gdp_agent_runtime" -Args @("--help")) {
  Write-Host "[GDP MVP Smoke] gdp_agent_runtime --help passed"
  $entryChecked = $true
}

if (-not $entryChecked) {
  python -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('loguru') else 1)"
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[GDP MVP Smoke] skip module help: dependency 'loguru' not installed"
  } else {
    $env:PYTHONPATH = "src"
    python -m alias.cli --help
    python -m alias.server.alias_agent_app --help
    Write-Host "[GDP MVP Smoke] module help commands passed"
  }
}

Write-Host ""
Write-Host "[GDP MVP Smoke] Manual runtime checks:"
Write-Host "  1) gdp_agent run --mode general --task ""hello"""
Write-Host "  2) gdp_agent run --mode browser --task ""open example.com and summarize"""
Write-Host ""
Write-Host "[GDP MVP Smoke] Optional legacy worker compatibility:"
Write-Host "  `$env:GDP_ENABLE_LEGACY_WORKERS=1"
