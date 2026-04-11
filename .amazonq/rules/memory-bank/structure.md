# Project Structure

## Directory Organization

```
Vitreos/
├── .amazonq/               # Amazon Q rules and memory bank
├── .github/                # GitHub workflows
├── config/                 # Configuration modules
├── fonts/                  # Custom font assets (Share Tech Mono, VT323)
├── legacy_pyqt/            # Archived PyQt6 reference implementation (READ-ONLY)
├── vitreos_main_v3.py      # Main application entry point
├── vitreos_theme.py        # Figma design system (colors, fonts, stylesheet)
├── vitreos_widgets.py      # Custom PyQt6 widgets (bars, frames, log)
├── vitreos_modules.py      # Dashboard monitoring modules (CPU, GPU, etc.)
├── vitreos_telemetry.py    # QThread hardware data collection
├── vitreos_db.py           # SQLite database module
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## Core Components

### 1. Main Application (`vitreos_main_v3.py`)
**Purpose**: Application entry point with frameless window and dashboard layout

**Key Classes**:
- `VitreosMainWindow` - Main window with frameless design and custom layout
  - 232px fixed sidebar (SystemPulseLog)
  - 2x3 grid dashboard (monitoring modules)
  - Drag support for frameless window
  - Telemetry worker integration

**Responsibilities**:
- Initialize PyQt6 application
- Create frameless window with Liquid Glass styling
- Build 2x3 dashboard grid layout
- Start telemetry worker thread
- Route hardware data to monitoring modules
- Handle log messages from telemetry worker

---

### 2. Theme Engine (`vitreos_theme.py`)
**Purpose**: Figma design system implementation with color palette and typography

**Key Components**:
- `VITREOS_COLORS` - 30+ color tokens (purple, orange, cyan, green, backgrounds, borders, text)
- `VITREOS_FONTS` - Font family definitions (Share Tech Mono, VT323)
- `FONT_SIZES` - Typography scale (logo: 44pt, title: 14pt, micro: 7pt)
- `VITREOS_STYLESHEET` - Global QSS stylesheet with Liquid Glass effects

**Functions**:
- `load_google_fonts()` - Load custom fonts from fonts/ directory
- `get_font()` - Get configured QFont with fallback support
- `get_color()` - Get QColor from palette
- `initialize_theme()` - Initialize theme system

---

### 3. Custom Widgets (`vitreos_widgets.py`)
**Purpose**: Specialized PyQt6 components matching Figma specifications

**Key Widgets**:
- `VitreosSegmentedBar` - Horizontal LED progress indicator (22 segments, auto-alert coloring)
- `VitreosVerticalBar` - Vertical LED bar for CPU core grid (7 segments, bottom-to-top fill)
- `VitreosWinFrame` - Container with title bar, indicators, and scanline overlay
- `SystemPulseLog` - Fixed 232px sidebar with VITREOS logo, scrolling log, and blinking cursor

**Features**:
- Glow effects on active segments
- Alert zone coloring (orange when >80% threshold)
- Scanline overlay pattern (every 4px)
- Terminal-style log with HTML formatting
- Blinking cursor animation (530ms interval)

---

### 4. Monitoring Modules (`vitreos_modules.py`)
**Purpose**: Dashboard widgets for 2x3 grid layout

**Implemented Modules**:
- `CpuMonitor` - AMD Ryzen 7 5700X dashboard with per-core activity grid (16 cores)
- `GpuMonitor` - NVIDIA RTX 3060 dashboard with usage, VRAM, clocks, power, temp

**Placeholder Modules** (to be implemented):
- `ThermalCtrl` - Thermal monitoring widget
- `StorageArray` - Storage monitoring widget
- `MemoryArray` - Memory monitoring widget
- `NetInterface` - Network monitoring widget

**Grid Layout**:
```
Row 1: [StorageArray] [CpuMonitor] [ThermalCtrl]
Row 2: [MemoryArray]  [GpuMonitor] [NetInterface]
```

---

### 5. Telemetry Worker (`vitreos_telemetry.py`)
**Purpose**: QThread-based hardware data collection

**Key Classes**:
- `TelemetryWorker` - Background thread for hardware monitoring
  - Emits `data_ready` signal every 1 second
  - Emits `log_message` signal for sidebar log
  - Emits `error_occurred` signal for error handling

**Data Collection Methods**:
- `_get_cpu_data()` - psutil CPU metrics (load, temp, clock, per-core)
- `_get_gpu_data()` - pynvml GPU metrics (usage, VRAM, clocks, power, temp, fans)
- `_get_memory_data()` - psutil memory metrics (used, total, slots)
- `_get_storage_data()` - psutil storage metrics (drives, usage, I/O)
- `_get_network_data()` - psutil network metrics (download, upload, latency)
- `_get_thermal_data()` - psutil thermal metrics (temps, fans)

**Features**:
- Graceful degradation if NVML unavailable
- Non-blocking operation (runs in separate thread)
- Auto-cleanup on shutdown (NVML shutdown)

---

### 6. Database Module (`vitreos_db.py`)
**Purpose**: SQLite database for historical data storage

**Key Classes**:
- `VitreosDB` - Database manager with QThread worker
- `DatabaseWorker` - Background worker for write operations

**Tables**:
- `hardware_log` - CPU, RAM, GPU, Disk metrics with timestamps
- `process_rules` - Process tuning rules (priority, affinity)

**Features**:
- Thread-safe operations (`check_same_thread=False`)
- Background writes via QThread worker
- Signal/slot architecture for non-blocking writes

---

### 7. Configuration System (`config/`)
**Purpose**: Centralized settings and webhook management

**Files**:
- `settings.json` - Discord webhook URL, monitoring intervals, feature toggles
- `webhooks.json` - Multi-channel Discord webhook routing
- `settings.py` - Configuration loader module
- `webhooks.py` - Webhook dispatcher module
- `__init__.py` - Package initialization with `__all__` exports

---

### 8. Legacy PyQt6 Reference (`legacy_pyqt/`)
**Purpose**: Original standalone desktop application (READ-ONLY)

**Status**: Preserved as reference for core logic, not actively developed

**Key Files**:
- `vitreos_main.py` - Original main application
- `vitreos_workers.py` - Hardware monitoring workers
- `vitreos_core_ui.py` - Core UI framework
- `tabs/` - Modular tab components (10 tabs)

---

## Architectural Patterns

### QThread Architecture
```
┌─────────────────────────────────────────┐
│      MAIN WINDOW (UI Thread)            │
│  ┌───────────────────────────────────┐  │
│  │   SystemPulseLog (232px sidebar)  │  │
│  │   • VITREOS logo                  │  │
│  │   • Scrolling log                 │  │
│  │   • Blinking cursor               │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   2x3 Dashboard Grid              │  │
│  │   • CpuMonitor                    │  │
│  │   • GpuMonitor                    │  │
│  │   • ThermalCtrl                   │  │
│  │   • StorageArray                  │  │
│  │   • MemoryArray                   │  │
│  │   • NetInterface                  │  │
│  └───────────────────────────────────┘  │
│              ↕ Signals/Slots            │
│  ┌───────────────────────────────────┐  │
│  │  TELEMETRY WORKER (QThread)       │  │
│  │  • psutil Hardware Collection     │  │
│  │  • pynvml GPU Monitoring          │  │
│  │  • 1-second polling interval      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Component Relationships

**Main Window → Telemetry Worker**:
- Starts worker thread on initialization
- Connects `data_ready` signal to `_update_modules()` slot
- Connects `log_message` signal to sidebar `append_log()` method

**Telemetry Worker → Hardware APIs**:
- `psutil` for CPU, RAM, Disk, Network metrics
- `pynvml` for NVIDIA GPU deep metrics
- Graceful fallback if NVML unavailable

**Monitoring Modules → Data Updates**:
- Each module implements `update_data(data: Dict[str, Any])` method
- Main window routes telemetry data to appropriate modules
- Modules update UI elements (labels, bars) with fresh data

---

## Design Principles

1. **No Root Clutter**: Consolidate logic into existing modules, avoid temporary files
2. **No Redundancy**: Never create .backup, .old, or _v2 files
3. **Logic Preservation**: Treat `legacy_pyqt/` as read-only reference
4. **Zero One-Offs**: No temporary test scripts or fix-it batch files
5. **Automatic Cleanup**: Delete `__pycache__` and build artifacts after tasks

---

## Launch Command

```bash
python vitreos_main_v3.py
```

**Requirements**:
- Python 3.8+
- PyQt6
- psutil
- nvidia-ml-py (optional, for GPU monitoring)
