# -*- mode: python ; coding: utf-8 -*-
"""
Vitreos.spec - PyInstaller Specification File
Builds a standalone, native Windows executable (Vitreos.exe).
Explicitly bundles the PyO3 Rust FFI backend (vitreos_pulse.pyd).
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
project_root = Path(globals().get('SPECPATH', os.getcwd())).resolve()

# 1. Locate the compiled PyO3 Rust FFI binary (vitreos_pulse.pyd)
binaries = []
pulse_pyd_found = False

# Search in Python environment site-packages
try:
    import vitreos_pulse
    pulse_file = getattr(vitreos_pulse, '__file__', None)
    if pulse_file:
        pulse_dir = Path(pulse_file).parent
        for pyd in pulse_dir.glob("*.pyd"):
            binaries.append((str(pyd), 'vitreos_pulse'))
            pulse_pyd_found = True
        for dll in pulse_dir.glob("*.dll"):
            binaries.append((str(dll), 'vitreos_pulse'))
except Exception as e:
    print(f"[SPEC] Warning during dynamic vitreos_pulse lookup: {e}")

# Fallback explicit filesystem search
if not pulse_pyd_found:
    search_paths = [
        project_root / ".venv" / "Lib" / "site-packages" / "vitreos_pulse",
        project_root / "vitreos_pulse_backend" / "target" / "release",
        project_root / "vitreos_pulse" / "target" / "release",
    ]
    for sp in search_paths:
        if sp.exists():
            for pyd in sp.glob("*.pyd"):
                binaries.append((str(pyd), 'vitreos_pulse'))
                pulse_pyd_found = True
                print(f"[SPEC] Found vitreos_pulse binary at: {pyd}")

print(f"[SPEC] Registered Rust FFI Binaries: {binaries}")

# 2. Bundled Read-Only Assets & Default Config
datas = [
    (str(project_root / 'assets'), 'assets'),
    (str(project_root / 'config'), 'config'),
]

# 3. Explicit Hidden Imports
hiddenimports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'psutil',
    'pynvml',
    'pypresence',
    'vitreos_pulse',
    'config',
    'config.settings',
    'src.core.schemas',
    'src.core.paths',
    'src.core.vitreos_db',
    'src.core.vitreos_telemetry_rust',
    'src.core.vitreos_telemetry_pull',
    'src.core.vitreos_presence',
    'src.core.vitreos_bridge',
]
hiddenimports += collect_submodules('PyQt6')
hiddenimports += collect_submodules('src')

a = Analysis(
    [str(project_root / 'run.py')],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'streamlit', 'pandas', 'pydeck', 'altair', 'plotly'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Vitreos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed GUI - no black console popup
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'assets' / 'logo.ico'),
)
