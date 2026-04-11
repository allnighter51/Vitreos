# Font Installation Required

## Missing Fonts
The following fonts are required but not currently installed:
- Share Tech Mono (ShareTechMono-Regular.ttf)
- VT323 (VT323-Regular.ttf)

## Download Instructions

### Option 1: Google Fonts (Recommended)
1. Visit https://fonts.google.com/specimen/Share+Tech+Mono
2. Click "Download family"
3. Extract ShareTechMono-Regular.ttf to `assets/fonts/`

4. Visit https://fonts.google.com/specimen/VT323
5. Click "Download family"
6. Extract VT323-Regular.ttf to `assets/fonts/`

### Option 2: Direct Links
```bash
# Share Tech Mono
curl -o "assets/fonts/ShareTechMono-Regular.ttf" "https://github.com/google/fonts/raw/main/ofl/sharetechmono/ShareTechMono-Regular.ttf"

# VT323
curl -o "assets/fonts/VT323-Regular.ttf" "https://github.com/google/fonts/raw/main/ofl/vt323/VT323-Regular.ttf"
```

## Current Fallback
The application will use **Segoe UI Variable** or **Consolas** as fallback fonts until the custom fonts are installed.

## Verification
After installing fonts, run:
```bash
python run.py
```

You should see:
```
[VITREOS THEME] Loaded font: Share Tech Mono from C:\...\assets\fonts\ShareTechMono-Regular.ttf
[VITREOS THEME] Loaded font: VT323 from C:\...\assets\fonts\VT323-Regular.ttf
```

Instead of:
```
[VITREOS THEME] Font file not found: ...
[VITREOS THEME] WARNING: No custom fonts loaded, using fallbacks
```
