@echo off
title Vitreos Hardware Forensics Dashboard
if exist "dist\Vitreos.exe" (
    echo Launching native standalone Vitreos.exe...
    start "" "dist\Vitreos.exe"
) else (
    echo Launching development Vitreos via run.py...
    if exist ".venv\Scripts\python.exe" (
        .venv\Scripts\python.exe run.py
    ) else (
        python run.py
    )
)
