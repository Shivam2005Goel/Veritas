# ==============================================================================
# VERITAS: Fact Knowledge Layer - Single-Command Launcher
# Superjoin VIT 2026 Engineering Intern Hiring Assignment
# ==============================================================================

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "           VERITAS - Multi-Document Fact Knowledge Layer          " -ForegroundColor Yellow
Write-Host "       Grounding * Evidence Highlighting * Cross-Doc Reconciler   " -ForegroundColor DarkCyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python 3 is not found in PATH." -ForegroundColor Red
    exit 1
}

# Check Node / NPM
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node / NPM is not found in PATH." -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$BackendProcess = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--reload" -WorkingDirectory $BackendDir -PassThru -WindowStyle Minimized

Write-Host "[2/3] Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Green
$FrontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $FrontendDir -PassThru -WindowStyle Minimized

Write-Host "[3/3] Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

Write-Host ""
Write-Host "-----------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "  Veritas is running!" -ForegroundColor Green
Write-Host "  * Web Application UI:       http://localhost:3000" -ForegroundColor White
Write-Host "  * Interactive Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "  * REST API Health:          http://127.0.0.1:8000/api/facts" -ForegroundColor White
Write-Host "-----------------------------------------------------------------" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starter Datasets Available:" -ForegroundColor Yellow
Write-Host "  - Delhivery (3 filings: DRHP, FY24 Annual, Q1-FY25 Result)"
Write-Host "  - India Macroeconomy (3 reports: RBI Bulletin, MoSPI CPI, IMF WEO)"
Write-Host ""
Write-Host "Press [Ctrl+C] or close this window to exit and stop processes." -ForegroundColor Gray
Write-Host ""

try {
    # Keep script open and monitor processes
    while (-not $BackendProcess.HasExited -and -not $FrontendProcess.HasExited) {
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host "`nStopping Veritas services..." -ForegroundColor Yellow
    if ($BackendProcess -and -not $BackendProcess.HasExited) { Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) { Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue }
    Write-Host "Services stopped cleanly." -ForegroundColor Green
}
