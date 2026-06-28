$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$OutputRoot = Join-Path $RepoRoot "eoh_go_workspace\reports\auto_experiment_reports"
$StateRoot = Join-Path $RepoRoot "eoh_go_workspace\local_runs\glm_ablation_24"
$StatePath = Join-Path $StateRoot "state.json"
$LogPath = Join-Path $StateRoot "runner.log"
$GlmWrapper = Join-Path $PSScriptRoot "run_with_glm.ps1"

New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null
Set-Location $RepoRoot
. $GlmWrapper

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class ExecutionState {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint flags);
}
"@

function Write-State([string]$Status, [string]$Suite, [int]$ExitCode = 0) {
    @{
        status = $Status
        suite = $Suite
        exit_code = $ExitCode
        updated_at = (Get-Date).ToString("o")
        branch = "run_codex"
        provider = "opencode-go"
        model = "glm-5.2"
    } | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath $StatePath
}

function Invoke-Suite([string]$Name, [string]$Manifest) {
    Write-State "running" $Name
    "[$(Get-Date -Format o)] starting $Name" | Tee-Object -FilePath $LogPath -Append
    & python -u -m eoh_go.experiments.batch_runner `
        --manifest $Manifest `
        --output-dir $OutputRoot `
        --resume `
        --force 2>&1 | Tee-Object -FilePath $LogPath -Append
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-State "failed" $Name $code
        throw "$Name failed with exit code $code"
    }
    Write-State "completed" $Name
    "[$(Get-Date -Format o)] completed $Name" | Tee-Object -FilePath $LogPath -Append
}

[ExecutionState]::SetThreadExecutionState(0x80000001) | Out-Null
try {
    Invoke-Suite `
        "tsp" `
        "eoh_go_workspace/experiments/manifests/rag_ablation_4arm_tsp_codex_glm52.json"
    Invoke-Suite `
        "cvrp" `
        "eoh_go_workspace/experiments/manifests/rag_ablation_4arm_cvrp_codex_glm52.json"
    Write-State "completed" "all"
} catch {
    $_ | Out-String | Tee-Object -FilePath $LogPath -Append
    throw
} finally {
    [ExecutionState]::SetThreadExecutionState(0x80000000) | Out-Null
}
