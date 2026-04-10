# VITREOS SENTINEL - Emergency Consolidation Script
# Merges vitreos-ui subfolder into root directory

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   VITREOS SENTINEL - CONSOLIDATION PROTOCOL       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Define paths
$rootPath = "C:\Users\domco\Workspace\vitreos"
$subfolderPath = "$rootPath\vitreos-ui"

# Verify paths exist
if (-not (Test-Path $rootPath)) {
    Write-Host "[CRITICAL] Root path does not exist: $rootPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $subfolderPath)) {
    Write-Host "[WARNING] Subfolder not found: $subfolderPath" -ForegroundColor Yellow
    Write-Host "[INFO] Assuming consolidation already complete or different structure" -ForegroundColor Gray
    exit 0
}

Write-Host "[PHASE 1] Moving configuration files to root..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────" -ForegroundColor Gray

# Critical files to move
$filesToMove = @(
    "package.json",
    "package-lock.json",
    "vite.config.ts",
    "tsconfig.json",
    "postcss.config.mjs",
    "tailwind.config.js",
    "index.html",
    ".gitignore",
    ".env"
)

foreach ($file in $filesToMove) {
    $sourcePath = "$subfolderPath\$file"
    $destPath = "$rootPath\$file"
    
    if (Test-Path $sourcePath) {
        # Backup existing file in root if it exists
        if (Test-Path $destPath) {
            $backupPath = "$destPath.backup"
            Write-Host "  [BACKUP] Existing $file → $file.backup" -ForegroundColor Yellow
            Move-Item -Path $destPath -Destination $backupPath -Force
        }
        
        Write-Host "  [MOVE] $file → root" -ForegroundColor Green
        Move-Item -Path $sourcePath -Destination $destPath -Force
    } else {
        Write-Host "  [SKIP] $file not found in subfolder" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "[PHASE 2] Cleaning up node_modules..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────" -ForegroundColor Gray

# Remove old node_modules from both locations
$nodeModulesRoot = "$rootPath\node_modules"
$nodeModulesSub = "$subfolderPath\node_modules"

if (Test-Path $nodeModulesRoot) {
    Write-Host "  [DELETE] Removing root node_modules..." -ForegroundColor Red
    Remove-Item -Path $nodeModulesRoot -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Root node_modules removed" -ForegroundColor Green
}

if (Test-Path $nodeModulesSub) {
    Write-Host "  [DELETE] Removing subfolder node_modules..." -ForegroundColor Red
    Remove-Item -Path $nodeModulesSub -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Subfolder node_modules removed" -ForegroundColor Green
}

Write-Host ""
Write-Host "[PHASE 3] Removing empty vitreos-ui folder..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────" -ForegroundColor Gray

if (Test-Path $subfolderPath) {
    $remainingItems = Get-ChildItem -Path $subfolderPath -Force -ErrorAction SilentlyContinue
    
    if ($remainingItems.Count -eq 0) {
        Remove-Item -Path $subfolderPath -Force
        Write-Host "  [OK] vitreos-ui folder removed" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] vitreos-ui still contains files:" -ForegroundColor Yellow
        $remainingItems | ForEach-Object { 
            Write-Host "    • $($_.Name)" -ForegroundColor Gray 
        }
        Write-Host "  [INFO] Manual cleanup may be required" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[PHASE 4] Updating package.json scripts..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────" -ForegroundColor Gray

$packageJsonPath = "$rootPath\package.json"

if (Test-Path $packageJsonPath) {
    $packageJson = Get-Content $packageJsonPath -Raw | ConvertFrom-Json
    
    # Ensure scripts object exists
    if (-not $packageJson.scripts) {
        $packageJson | Add-Member -MemberType NoteProperty -Name "scripts" -Value ([PSCustomObject]@{})
    }
    
    # Add/update scripts
    $scripts = @{
        "dev" = "vite"
        "build" = "vite build"
        "preview" = "vite preview"
        "tauri" = "tauri"
        "tauri:dev" = "tauri dev"
        "tauri:build" = "tauri build"
    }
    
    foreach ($key in $scripts.Keys) {
        if ($packageJson.scripts.PSObject.Properties.Name -contains $key) {
            $packageJson.scripts.$key = $scripts[$key]
            Write-Host "  [UPDATE] Script '$key' updated" -ForegroundColor Cyan
        } else {
            $packageJson.scripts | Add-Member -MemberType NoteProperty -Name $key -Value $scripts[$key]
            Write-Host "  [ADD] Script '$key' added" -ForegroundColor Green
        }
    }
    
    # Ensure Tauri dependencies
    if (-not $packageJson.dependencies) {
        $packageJson | Add-Member -MemberType NoteProperty -Name "dependencies" -Value ([PSCustomObject]@{})
    }
    if (-not $packageJson.devDependencies) {
        $packageJson | Add-Member -MemberType NoteProperty -Name "devDependencies" -Value ([PSCustomObject]@{})
    }
    
    # Add Tauri packages if missing
    if (-not ($packageJson.dependencies.PSObject.Properties.Name -contains "@tauri-apps/api")) {
        $packageJson.dependencies | Add-Member -MemberType NoteProperty -Name "@tauri-apps/api" -Value "^2.0.0"
        Write-Host "  [ADD] Dependency @tauri-apps/api" -ForegroundColor Green
    }
    
    if (-not ($packageJson.devDependencies.PSObject.Properties.Name -contains "@tauri-apps/cli")) {
        $packageJson.devDependencies | Add-Member -MemberType NoteProperty -Name "@tauri-apps/cli" -Value "^2.0.0"
        Write-Host "  [ADD] DevDependency @tauri-apps/cli" -ForegroundColor Green
    }
    
    # Save updated package.json with proper formatting
    $packageJson | ConvertTo-Json -Depth 10 | Set-Content $packageJsonPath
    Write-Host "  [OK] package.json updated successfully" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] package.json not found at root!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[PHASE 5] Creating main.tsx entry point..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────" -ForegroundColor Gray

$mainTsxPath = "$rootPath\src\main.tsx"
$mainTsxContent = @"
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './app/App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"@

# Ensure src directory exists
$srcPath = "$rootPath\src"
if (-not (Test-Path $srcPath)) {
    New-Item -Path $srcPath -ItemType Directory -Force | Out-Null
    Write-Host "  [CREATE] src directory created" -ForegroundColor Green
}

Set-Content -Path $mainTsxPath -Value $mainTsxContent -Force
Write-Host "  [OK] main.tsx created at src/main.tsx" -ForegroundColor Green

Write-Host ""
Write-Host "[PHASE 6] Updating index.html..." -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────" -ForegroundColor Gray

$indexHtmlPath = "$rootPath\index.html"

if (Test-Path $indexHtmlPath) {
    $indexHtml = Get-Content $indexHtmlPath -Raw
    
    # Update script tag to point to correct entry
    if ($indexHtml -match '<script[^>]*src="[^"]*"[^>]*></script>') {
        $indexHtml = $indexHtml -replace '<script[^>]*src="[^"]*"[^>]*></script>', '<script type="module" src="/src/main.tsx"></script>'
        Write-Host "  [UPDATE] Script tag updated to /src/main.tsx" -ForegroundColor Cyan
    } else {
        # Add script tag if missing
        $indexHtml = $indexHtml -replace '</body>', '  <script type="module" src="/src/main.tsx"></script>`n  </body>'
        Write-Host "  [ADD] Script tag added" -ForegroundColor Green
    }
    
    Set-Content -Path $indexHtmlPath -Value $indexHtml -Force
    Write-Host "  [OK] index.html updated" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] index.html not found!" -ForegroundColor Red
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          CONSOLIDATION COMPLETE                    ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. cd C:\Users\domco\Workspace\vitreos" -ForegroundColor White
Write-Host "  2. npm install" -ForegroundColor White
Write-Host "  3. npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "For Tauri development:" -ForegroundColor Yellow
Write-Host "  npm run tauri:dev" -ForegroundColor White
Write-Host ""
