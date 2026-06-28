$ErrorActionPreference = "Stop"

$AuthPath = Join-Path $env:USERPROFILE ".local\share\opencode\auth.json"
if (-not (Test-Path -LiteralPath $AuthPath)) {
    throw "opencode auth file not found: $AuthPath"
}

$auth = Get-Content -LiteralPath $AuthPath -Raw | ConvertFrom-Json
$provider = $auth.'opencode-go'
if (-not $provider) {
    throw "provider 'opencode-go' not found in opencode auth file"
}

$apiKey = "$($provider.key)".Trim()
if (-not $apiKey) {
    throw "opencode-go API key is empty"
}

$env:DEEPSEEK_API_KEY = $apiKey
$env:DEEPSEEK_API_ENDPOINT = "https://opencode.ai/zen/go/v1/chat/completions"
$env:DEEPSEEK_MODEL = "glm-5.2"

Write-Host "glm-5.2 API loaded from opencode-go provider (key hidden)."
Write-Host "DEEPSEEK_API_ENDPOINT = $env:DEEPSEEK_API_ENDPOINT"
Write-Host "DEEPSEEK_MODEL        = $env:DEEPSEEK_MODEL"

if ($args.Count -eq 0) {
    Write-Host ""
    Write-Host "No command supplied. Env vars set for this process only."
    Write-Host "Example:"
    Write-Host "  .\scripts\run_with_glm.ps1 python -m eoh_go.experiments.grids.arrival_scale_grid --llm-model glm-5.2 ..."
    Write-Host "  .\scripts\run_with_glm.ps1 python -m eoh_go.experiments.eoh_single_runner --llm-model glm-5.2 ..."
    return
}

$exe = $args[0]
if ($args.Count -gt 1) {
    $rest = @($args[1..($args.Count - 1)])
} else {
    $rest = @()
}

& $exe @rest
$code = $LASTEXITCODE
if ($null -ne $code) { exit $code }
