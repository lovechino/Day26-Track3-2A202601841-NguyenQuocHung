# Start Day26 Lab 04 - Weather Agent with MCP Server
# Requires: GOOGLE_API_KEY, GEMINI_API_KEY, WEATHERAPI_KEY in .env files

param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$repoRoot = "E:\AIlearn\Day26-Track3-2A202601841-NguyenQuocHung"
$mcpServerDir = "$repoRoot\04-lab\mcp-server"
$mcpClientDir = "$repoRoot\04-lab\mcp-client"

Write-Host "=== Day26 Lab 04 - Weather Agent Startup ===" -ForegroundColor Cyan

# Load environment variables
$serverEnv = "$mcpServerDir\.env"
$clientEnv = "$mcpClientDir\.env"

function Load-EnvFile($path) {
    if (Test-Path $path) {
        $envs = Get-Content $path | Where-Object { $_ -match "^[A-Z_]+=" }
        foreach ($line in $envs) {
            $parts = $line.Split("=", 2)
            if ($parts.Count -eq 2) { Set-Item "Env:$($parts[0])" -Value $parts[1] }
        }
        return $true
    }
    return $false
}

Load-EnvFile $serverEnv
Load-EnvFile $clientEnv
Write-Host "Loaded .env files"

# Check required keys
$required = @("GOOGLE_API_KEY", "GEMINI_API_KEY", "WEATHERAPI_KEY")
$missing = $required | Where-Object { -not (Test-Path "Env:$_") }
if ($missing) {
    Write-Host "Missing env vars: $($missing -join ", ")" -ForegroundColor Red
    Write-Host "Please set in $serverEnv and $clientEnv" -ForegroundColor Yellow
    exit 1
}

# Kill existing processes on ports 8085, 8000
Write-Host "Cleaning up old processes..."
$ports = 8085, 8000
foreach ($port in $ports) {
    $pids = (netstat -ano | Select-String ":$port\s" | ForEach-Object { ($_ -split "\s+")[-1] }) | Select-Object -Unique
    foreach ($pid in $pids) {
        if ($pid -and $pid -ne "0") {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "  Killed PID $pid on port $port"
        }
    }
}

# Start MCP Server
Write-Host "`nStarting MCP Server on :8085..." -ForegroundColor Green
$mcpProc = Start-Process -FilePath "python" -ArgumentList "weather.py" -WorkingDirectory $mcpServerDir `
    -PassThru -WindowStyle Hidden
Write-Host "  MCP Server PID: $($mcpProc.Id)"

# Wait for server to be ready
Start-Sleep -Seconds 4
for ($i=0; $i -lt 15; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8085/mcp" -Method Post `
            -Body '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}' `
            -ContentType "application/json" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($r.StatusCode -eq 200) { Write-Host "  MCP Server ready!" -ForegroundColor Green; break }
    } catch { }
    Start-Sleep -Seconds 1
}

# Start ADK Web
Write-Host "`nStarting ADK Web on :8000..." -ForegroundColor Green
$adkProc = Start-Process -FilePath "python" -ArgumentList "-m", "google.adk.cli", "web", "--port", "8000" `
    -WorkingDirectory $mcpClientDir -PassThru -WindowStyle Hidden
Write-Host "  ADK Web PID: $($adkProc.Id)"

Start-Sleep -Seconds 5
Write-Host "`n=== Services Running ===" -ForegroundColor Cyan
Write-Host "  MCP Server:  http://localhost:8085/mcp  (PID $($mcpProc.Id))"
Write-Host "  ADK Web UI:  http://127.0.0.1:8000     (PID $($adkProc.Id))"
Write-Host ""
Write-Host "Open http://127.0.0.1:8000 in browser" -ForegroundColor Yellow
Write-Host "Select 'weather_agent' and ask: 'Thời tiết Hà Nội?'"
Write-Host ""
Write-Host "Press Ctrl+C to stop all services..."

# Keep script running, forward Ctrl+C to children
try {
    while ($true) {
        if (-not (Get-Process -Id $mcpProc.Id -ErrorAction SilentlyContinue)) { Write-Host "MCP Server died!"; break }
        if (-not (Get-Process -Id $adkProc.Id -ErrorAction SilentlyContinue)) { Write-Host "ADK Web died!"; break }
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host "`nStopping services..."
    Stop-Process -Id $mcpProc.Id, $adkProc.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Done."
}
