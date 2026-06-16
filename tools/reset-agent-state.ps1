param(
    [string]$Agent = "",
    [string]$Timestamp = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $ScriptDir "..")
$InstancesDir = Join-Path $Root "instances"
$EnvPath = Join-Path $Root ".env"

function Say($Message) {
    Write-Host "[reset-agent-state] $Message"
}

function Assert-UnderRoot($Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    $rootFull = [System.IO.Path]::GetFullPath($Root)
    if (-not $full.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to touch path outside repository root: $full"
    }
    return $full
}

function Remove-PathIfExists($Path) {
    $full = Assert-UnderRoot $Path
    if (-not (Test-Path -LiteralPath $full)) {
        return
    }
    if ($DryRun) {
        Say "dry-run: would remove $full"
        return
    }
    Remove-Item -LiteralPath $full -Recurse -Force
    Say "removed $full"
}

function Get-AgentDirs {
    if (-not (Test-Path -LiteralPath $InstancesDir)) {
        throw "instances directory not found: $InstancesDir"
    }

    $dirs = Get-ChildItem -LiteralPath $InstancesDir -Directory |
        Where-Object { $_.Name -match '^agent\d+$' }

    if (-not [string]::IsNullOrWhiteSpace($Agent)) {
        $dirs = $dirs | Where-Object { $_.Name -eq $Agent }
        if (-not $dirs) {
            throw "Agent not found: $Agent"
        }
    }

    return $dirs | Sort-Object Name
}

function Upsert-EnvLine($Lines, $Key, $Value) {
    $pattern = "^\s*$([regex]::Escape($Key))="
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i] -match $pattern) {
            $Lines[$i] = "$Key=$Value"
            return $Lines
        }
    }
    $Lines.Add("$Key=$Value")
    return $Lines
}

function Update-DeviceIds($AgentDirs, $Stamp) {
    if (-not (Test-Path -LiteralPath $EnvPath)) {
        throw ".env not found: $EnvPath"
    }

    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($line in Get-Content -LiteralPath $EnvPath) {
        $lines.Add($line)
    }

    foreach ($dir in $AgentDirs) {
        if ($dir.Name -notmatch '^agent(\d+)$') {
            continue
        }
        $id = $Matches[1]
        $key = "AGENT${id}_MATRIX_DEVICE_ID"
        $value = "$($dir.Name)_$Stamp"
        $lines = Upsert-EnvLine $lines $key $value
        Say "$key=$value"
    }

    if ($DryRun) {
        Say "dry-run: would update $EnvPath"
        return
    }
    Set-Content -LiteralPath $EnvPath -Value $lines -Encoding UTF8
    Say "updated $EnvPath"
}

if ([string]::IsNullOrWhiteSpace($Timestamp)) {
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
}

if ($Timestamp -notmatch '^[A-Za-z0-9_-]+$') {
    throw "Timestamp may only contain letters, numbers, underscores, or hyphens."
}

$agentDirs = @(Get-AgentDirs)
if ($agentDirs.Count -eq 0) {
    throw "No agent directories found under $InstancesDir"
}

Say "target agents: $($agentDirs.Name -join ', ')"

foreach ($dir in $agentDirs) {
    $zeroClawDir = Join-Path $dir.FullName ".zeroclaw"
    Remove-PathIfExists (Join-Path $zeroClawDir "config.toml")
    Remove-PathIfExists (Join-Path $zeroClawDir "state")
    Remove-PathIfExists (Join-Path $zeroClawDir "data\state")
}

Update-DeviceIds $agentDirs $Timestamp
Say "done"
