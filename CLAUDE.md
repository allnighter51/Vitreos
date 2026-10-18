# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vitreos is a comprehensive PyQt6-based system monitoring suite with a Rust telemetry backend (vitreos_pulse). It provides real-time monitoring of CPU, GPU, memory, network, storage, and system processes through a 10-tab interface.

# Vitreos Project Guidelines

## Vision & Aesthetic
- **Style:** Grungy Y2K / Edgy Hacker. High-contrast, brutalist, system-heavy UI.
- **Philosophy:** Stoic engineering. Value efficiency, low overhead, and directness. 
- **FORBIDDEN:** "Liquid Glass" UI design. Do not suggest soft gradients, rounded "glassmorphism," or "modern-corporate" aesthetics.

## Technical Stack
- **Languages:** Rust (Core telemetry, NVML/hardware bindings), Python (Frontend/Orchestration).
- **Architecture:** 10-module modular PC monitoring system. 
- **Performance:** Maintain low CPU/RAM footprint.

## Coding Standards
- Use explicit error handling in Rust (avoid unwrap).
- Maintain strict modularity between the 10 core lobes.
- Always run `cargo check` and `pytest` before suggesting a fix is complete.

## Workflow
- Always `/plan` before executing multi-file edits.
- If a bug is found, trace the hardware dependency (NVML) before assuming it's a logic error.

## Running the Application

```bash
python src/main.py
```

The application requires a virtual environment with dependencies installed:
```bash
pip install -r requirements.txt
```

## Type Checking

This project uses Pyright with strict mode. Configuration is in `pyrightconfig.json`. Run:
```bash
pyright src/
```

## Architecture

### Entry Point
`src/main.py` contains `VitreosMainWindow` - the main application window with frameless design and custom 10-tab navigation.

### Core Telemetry Pipeline
1. **Rust Backend (`vitreos_pulse`)**: High-frequency hardware data collection via PyO3 FFI
2. **Telemetry Worker (`src/core/vitreos_telemetry_rust.py`)**: `RustTelemetryWorker` QThread that polls the Rust engine
3. **Schema Validation (`src/core/schemas.py`)**: Pydantic v2 models enforce type safety across the FFI boundary
4. **UI Dispatch**: Tab updates are dispatched based on `stack.currentIndex()` - only active tab + VITALS are updated per tick

### Ten Tabs
Located in `src/tabs/`:
- **Vitals**: CPU core monitoring with temperature, load, voltage
- **GPU Pro**: VRAM, clock speeds, power draw, fan RPM
- **Network**: Bandwidth, latency, socket forensics
- **Processes**: Process list ranked by CPU/Memory
- **Console**: Raw telemetry stream for debugging
- **SOC**: Security operations center with geo threat map
- **Storage**: NVMe/SSD health metrics
- **Tweaks**: OS performance optimizations
- **Remote**: Discord Rich Presence integration
- **Settings**: Polling rates, webhooks, UI preferences

### Key Patterns
- **Pydantic Base**: `VitreosBaseModel` in schemas.py provides frozen, extra-forbid immutable models
- **Signal/Slot**: PyQt6 signals connect telemetry worker to UI components
- **Tab Indices**: VITALS=0, GPU=1, NETWORK=2, PROCESSES=3, CONSOLE=4, SOC=5, STORAGE=6, TWEAKS=7, REMOTE=8, SETTINGS=9
- **Per-Tab Updates**: `_update_modules()` in main.py skips off-screen tabs for performance

### Configuration
Settings are stored in `config/settings.json` and loaded via `config/settings.py`:
- `monitoring.polling_interval_ms`: Telemetry poll rate (default 2000ms)
- `monitoring.enable_gpu/network/security`: Feature toggles
- `discord.webhook_url`: Alert webhook

## Key Files

- `src/main.py` - Application entry point, main window, 10-tab stack
- `src/core/vitreos_telemetry_rust.py` - Telemetry worker orchestration
- `src/core/schemas.py` - All Pydantic telemetry models
- `src/ui/vitreos_theme.py` - Color palette (`VITREOS_COLORS`) and stylesheet
- `src/ui/vitreos_sidebar.py` - Left sidebar with pulse log