# VITREOS SENTINEL - Emergency Cache Purge & Restart
# Clears all Vite caches and restarts development server

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Red
Write-Host "║   VITREOS SENTINEL - CACHE PURGE PROTOCOL         ║" -ForegroundColor Red
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Red
Write-Host ""

$rootPath = "C:\Users\domco\Workspace\vitreos"

# Navigate to root
Set-Location $rootPath

Write-Host "[PHASE 1] Terminating existing Vite processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*node*" -or $_.ProcessName -like "*vite*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "  [OK] Processes terminated" -ForegroundColor Green

Write-Host ""
Write-Host "[PHASE 2] Purging Vite cache..." -ForegroundColor Yellow

$viteCachePath = "$rootPath\node_modules\.vite"
if (Test-Path $viteCachePath) {
    Remove-Item -Path $viteCachePath -Recurse -Force
    Write-Host "  [OK] node_modules/.vite removed" -ForegroundColor Green
} else {
    Write-Host "  [SKIP] Vite cache not found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[PHASE 3] Clearing dist folder..." -ForegroundColor Yellow

$distPath = "$rootPath\dist"
if (Test-Path $distPath) {
    Remove-Item -Path $distPath -Recurse -Force
    Write-Host "  [OK] dist/ removed" -ForegroundColor Green
} else {
    Write-Host "  [SKIP] dist/ not found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[PHASE 4] Verifying critical files..." -ForegroundColor Yellow

$criticalFiles = @(
    "index.html",
    "src\main.tsx",
    "src\index.css",
    "src\app\App.tsx",
    "vite.config.ts",
    "package.json"
)

$allPresent = $true
foreach ($file in $criticalFiles) {
    $filePath = "$rootPath\$file"
    if (Test-Path $filePath) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] $file MISSING!" -ForegroundColor Red
        $allPresent = $false
    }
}

if (-not $allPresent) {
    Write-Host ""
    Write-Host "[CRITICAL] Missing files detected. Cannot start server." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[PHASE 5] Starting Vite development server..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host ""

# Start Vite in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootPath'; npm run dev"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          CACHE PURGE COMPLETE                      ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Development server starting in new window..." -ForegroundColor Yellow
Write-Host "Navigate to: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
