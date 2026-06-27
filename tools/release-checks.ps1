param(
  [switch]$SkipCompose,
  [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repo

Write-Host "== Secrets scan =="
$secretPattern = "sk-[A-Za-z0-9_-]{12,}|ghp_|gho_|glpat-|xox[baprs]-|BEGIN (RSA|OPENSSH|PRIVATE) KEY|Bearer\s+[A-Za-z0-9_.=-]{12,}"
$secretHits = rg -n $secretPattern . --glob '!prompts/**' --glob '!tools/release-checks.ps1' --glob '!config/*.local.yaml' --glob '!config/manager.yaml' --glob '!config/secrets.yaml' --glob '!instances/**' --glob '!config/generated/**' 2>$null
if ($LASTEXITCODE -eq 0) {
  Write-Error "Potential secrets found:`n$secretHits"
}
if ($LASTEXITCODE -gt 1) {
  Write-Error "rg failed during secrets scan."
}
Write-Host "No obvious secrets found."

if (-not $SkipCompose) {
  Write-Host "== Compose config =="
  docker compose config --quiet
}

Write-Host "== Backend tests =="
python -m unittest discover manager/backend/tests

if (-not $SkipFrontend) {
  Write-Host "== Frontend tests =="
  node -e "JSON.parse(require('fs').readFileSync('manager/frontend/src/locales/en.json','utf8')); JSON.parse(require('fs').readFileSync('manager/frontend/src/locales/zh-CN.json','utf8'));"
  node manager/frontend/tests/ui-foundation.test.mjs
}

Write-Host "Release checks passed."
