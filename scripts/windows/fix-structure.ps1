# VITREOS Directory Structure Recovery Script
# Moves configuration files from vitreos-ui subfolder to root

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VITREOS DIRECTORY STRUCTURE RECOVERY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Define paths
$rootPath = "C:\Users\domco\Workspace\vitreos"
$subfolderPath = "$rootPath\vitreos-ui"

# Verify paths exist
if (-not (Test-Path $rootPath)) {
    Write-Host "[ERROR] Root path does not exist: $rootPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $subfolderPath)) {
    Write-Host "[ERROR] Subfolder path does not exist: $subfolderPath" -ForegroundColor Red
    exit 1
}

Write-Host "[STEP 1] Moving configuration files to root..." -ForegroundColor Yellow

# Files to move
$filesToMove = @(
    "package.json",
    "package-lock.json",
    "vite.config.ts",
    "tsconfig.json",
    "postcss.config.mjs",
    "tailwind.config.js",
    "index.html"
)

foreach ($file in $filesToMove) {
    $sourcePath = "$subfolderPath\$file"
    $destPath = "$rootPath\$file"
    
    if (Test-Path $sourcePath) {
        Write-Host "  Moving: $file" -ForegroundColor Green
        Move-Item -Path $sourcePath -Destination $destPath -Force
    } else {
        Write-Host "  [SKIP] File not found: $file" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "[STEP 2] Moving node_modules to root..." -ForegroundColor Yellow

$nodeModulesSource = "$subfolderPath\node_modules"
$nodeModulesDest = "$rootPath\node_modules"

if (Test-Path $nodeModulesSource) {
    if (Test-Path $nodeModulesDest) {
        Write-Host "  Removing existing node_modules in root..." -ForegroundColor Gray
        Remove-Item -Path $nodeModulesDest -Recurse -Force
    }
    Write-Host "  Moving node_modules (this may take a moment)..." -ForegroundColor Green
    Move-Item -Path $nodeModulesSource -Destination $nodeModulesDest -Force
} else {
    Write-Host "  [SKIP] node_modules not found in subfolder" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[STEP 3] Updating package.json with Tauri scripts..." -ForegroundColor Yellow

$packageJsonPath = "$rootPath\package.json"

if (Test-Path $packageJsonPath) {
    $packageJson = Get-Content $packageJsonPath -Raw | ConvertFrom-Json
    
    # Add Tauri scripts
    if (-not $packageJson.scripts) {
        $packageJson | Add-Member -MemberType NoteProperty -Name "scripts" -Value @{}
    }
    
    $packageJson.scripts | Add-Member -MemberType NoteProperty -Name "tauri" -Value "tauri" -Force
    $packageJson.scripts | Add-Member -MemberType NoteProperty -Name "tauri:dev" -Value "tauri dev" -Force
    $packageJson.scripts | Add-Member -MemberType NoteProperty -Name "tauri:build" -Value "tauri build" -Force
    
    # Ensure dev and build scripts exist
    if (-not $packageJson.scripts.dev) {
        $packageJson.scripts | Add-Member -MemberType NoteProperty -Name "dev" -Value "vite" -Force
    }
    if (-not $packageJson.scripts.build) {
        $packageJson.scripts | Add-Member -MemberType NoteProperty -Name "build" -Value "vite build" -Force
    }
    
    # Add Tauri dependencies
    if (-not $packageJson.dependencies) {
        $packageJson | Add-Member -MemberType NoteProperty -Name "dependencies" -Value @{}
    }
    if (-not $packageJson.devDependencies) {
        $packageJson | Add-Member -MemberType NoteProperty -Name "devDependencies" -Value @{}
    }
    
    $packageJson.dependencies | Add-Member -MemberType NoteProperty -Name "@tauri-apps/api" -Value "^2.0.0" -Force
    $packageJson.devDependencies | Add-Member -MemberType NoteProperty -Name "@tauri-apps/cli" -Value "^2.0.0" -Force
    
    # Save updated package.json
    $packageJson | ConvertTo-Json -Depth 10 | Set-Content $packageJsonPath
    Write-Host "  package.json updated successfully" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] package.json not found at root" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[STEP 4] Updating vite.config.ts paths..." -ForegroundColor Yellow

$viteConfigPath = "$rootPath\vite.config.ts"

if (Test-Path $viteConfigPath) {
    $viteConfig = Get-Content $viteConfigPath -Raw
    
    # Update paths if needed (assuming src is now at root level)
    # This is a basic replacement - adjust if your structure differs
    $viteConfig = $viteConfig -replace "'\./src'", "'./src'"
    
    Set-Content -Path $viteConfigPath -Value $viteConfig
    Write-Host "  vite.config.ts paths verified" -ForegroundColor Green
} else {
    Write-Host "  [SKIP] vite.config.ts not found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[STEP 5] Cleaning up empty subfolder..." -ForegroundColor Yellow

if (Test-Path $subfolderPath) {
    $remainingItems = Get-ChildItem -Path $subfolderPath -Force
    if ($remainingItems.Count -eq 0) {
        Remove-Item -Path $subfolderPath -Force
        Write-Host "  Removed empty vitreos-ui folder" -ForegroundColor Green
    } else {
        Write-Host "  [INFO] vitreos-ui folder still contains files:" -ForegroundColor Yellow
        $remainingItems | ForEach-Object { Write-Host "    - $($_.Name)" -ForegroundColor Gray }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RECOVERY COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. cd C:\Users\domco\Workspace\vitreos" -ForegroundColor White
Write-Host "  2. npm install" -ForegroundColor White
Write-Host "  3. npm run tauri:dev" -ForegroundColor White
Write-Host ""
