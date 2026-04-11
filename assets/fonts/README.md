# Vitreos Font Installation

## Required Fonts

The Vitreos UI requires the following Google Fonts:

1. **Share Tech Mono** - Primary monospace font
2. **VT323** - Display/logo font

## Installation Instructions

### Option 1: Download from Google Fonts

1. Visit https://fonts.google.com/specimen/Share+Tech+Mono
2. Click "Download family"
3. Extract `ShareTechMono-Regular.ttf` to this folder

4. Visit https://fonts.google.com/specimen/VT323
5. Click "Download family"
6. Extract `VT323-Regular.ttf` to this folder

### Option 2: System Installation (Windows)

1. Download the fonts from Google Fonts
2. Right-click each `.ttf` file
3. Select "Install for all users"
4. Fonts will be available system-wide

### Fallback Fonts

If custom fonts are not installed, Vitreos will use:
- **Consolas** (fallback for Share Tech Mono)
- **Courier New** (fallback for VT323)

## Verification

Run the application - you should see:
```
[VITREOS THEME] Loaded font: Share Tech Mono
[VITREOS THEME] Loaded font: VT323
```

If fonts fail to load, fallback fonts will be used automatically.
