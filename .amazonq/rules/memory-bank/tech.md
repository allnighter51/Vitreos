# Technology Stack

## Programming Languages

### Python 3.8+
**Usage**: Core application language for PyQt6 desktop application
**Location**: All `.py` files in root and subdirectories
**Environment**: Virtual environment recommended (`venv/`)

---

## Desktop Framework

### PyQt6
**Purpose**: Cross-platform desktop GUI framework
**Key Features**: Signals/slots, QThread, custom widgets, stylesheets (QSS)
**Entry Point**: `vitreos_main_v3.py`

**Core Modules Used**:
- `PyQt6.QtWidgets` - UI components (QMainWindow, QWidget, QLabel, etc.)
- `PyQt6.QtCore` - Core functionality (QThread, pyqtSignal, QTimer, Qt enums)
- `PyQt6.QtGui` - Graphics (QPainter, QFont, QColor, QPen, QBrush)

---

## Hardware Monitoring Libraries

### psutil
**Purpose**: Cross-platform system and process utilities
**Usage**: CPU, RAM, Disk, Network monitoring

**Key Functions**:
```python
psutil.cpu_percent(interval=0.1)  # CPU usage
psutil.cpu_percent(percpu=True)   # Per-core usage
psutil.cpu_freq()                 # CPU frequency
psutil.virtual_memory()           # RAM usage
psutil.disk_partitions()          # Disk partitions
psutil.disk_usage(path)           # Disk usage
psutil.disk_io_counters()         # Disk I/O
psutil.net_io_counters()          # Network I/O
psutil.sensors_temperatures()     # Temperature sensors (Linux)
psutil.sensors_fans()             # Fan sensors (Linux)
```

**Frequency**: Used in every telemetry collection cycle (1-second intervals)

---

### nvidia-ml-py (pynvml)
**Purpose**: NVIDIA Management Library Python bindings
**Usage**: GPU temperature, clock speeds, power draw, VRAM, fan speeds
**Requirement**: NVIDIA drivers and GPU

**Key Functions**:
```python
pynvml.nvmlInit()                                    # Initialize NVML
pynvml.nvmlDeviceGetHandleByIndex(0)                 # Get GPU handle
pynvml.nvmlDeviceGetUtilizationRates(handle)         # GPU/memory usage
pynvml.nvmlDeviceGetMemoryInfo(handle)               # VRAM usage
pynvml.nvmlDeviceGetTemperature(handle, 0)           # GPU temperature
pynvml.nvmlDeviceGetPowerUsage(handle)               # Power draw (mW)
pynvml.nvmlDeviceGetClockInfo(handle, NVML_CLOCK_GRAPHICS)  # Core clock
pynvml.nvmlDeviceGetClockInfo(handle, NVML_CLOCK_MEM)       # Memory clock
pynvml.nvmlDeviceGetFanSpeed(handle)                 # Fan speed (%)
pynvml.nvmlShutdown()                                # Cleanup
```

**Graceful Degradation**: Application continues without GPU monitoring if NVML unavailable

**Frequency**: Used in every telemetry collection cycle (1-second intervals)

---

## Database

### SQLite 3
**Purpose**: Historical data storage
**File**: `vitreos_history.db` (gitignored)
**Module**: `vitreos_db.py`

**Tables**:
```sql
CREATE TABLE hardware_log (
    timestamp TEXT PRIMARY KEY,
    cpu_temp REAL,
    cpu_usage REAL,
    gpu_temp REAL,
    gpu_usage REAL,
    ram_usage REAL
)

CREATE TABLE process_rules (
    process_name TEXT PRIMARY KEY,
    rule_type TEXT NOT NULL,
    rule_value TEXT NOT NULL
)
```

**Thread Safety**: `check_same_thread=False` for multi-threaded access

---

## Typography & Fonts

### Google Fonts
**Fonts Used**:
- **Share Tech Mono** - Primary monospace font for UI text
- **VT323** - Display font for VITREOS logo

**Fallbacks**:
- **Consolas** - Monospace fallback (Windows built-in)
- **Courier New** - Display fallback (Windows built-in)

**Loading**: Fonts loaded from `fonts/` directory via `QFontDatabase.addApplicationFont()`

---

## Design System

### Figma Design Tokens
**Color Palette**: 30+ color tokens defined in `VITREOS_COLORS` dict
- Primary: Purple (#A855F7, #7C3AED, #6B3FA0)
- Warning: Orange (#FF6B00), Red (#FF4444)
- Secondary: Cyan (#06B6D4), Green (#22C55E)
- Backgrounds: Dark grays (#0D0D0D, #0A0A0A, #111111)
- Borders: Subtle grays (#2A2A2A, #1E1E1E, #1A1A1A)
- Text: Light grays (#E2E8F0, #555555, #444444)

**Typography Scale**: 8 font sizes (logo: 44pt → micro: 7pt)

**Global Stylesheet**: QSS (Qt Style Sheets) with Liquid Glass effects

---

## Development Dependencies

### Python Packages (requirements.txt)
```
PyQt6          # Desktop GUI framework
psutil         # System monitoring
nvidia-ml-py   # NVIDIA GPU monitoring (optional)
```

### Optional Dependencies
- **requests** - For Discord webhook integration (legacy)
- **pywin32** - For Windows API access (legacy)
- **pypresence** - For Discord Rich Presence (legacy)

---

## Development Commands

### Run Application
```bash
python vitreos_main_v3.py
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Verify NVML Availability
```bash
nvidia-smi
```

---

## Build Requirements

### Windows Development Environment
- **Operating System**: Windows 10/11
- **Python**: 3.8+ (3.10+ recommended)
- **NVIDIA Drivers**: Latest for GPU monitoring (optional)

### Python Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Hardware APIs

### NVIDIA NVML (NVIDIA Management Library)
**Purpose**: Direct GPU hardware access
**Binding**: `nvidia-ml-py`
**Metrics**: Temperature, power draw, clock speeds, VRAM, fan speeds
**Requirement**: NVIDIA GPU with drivers installed

**Initialization Pattern**:
```python
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

if NVML_AVAILABLE:
    try:
        pynvml.nvmlInit()
        gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    except Exception as e:
        print(f"NVML init failed: {e}")
```

---

## Configuration Files

### Application Settings
- `config/settings.json` - Discord webhook URL, monitoring intervals, feature toggles
- `config/webhooks.json` - Multi-channel Discord webhook routing

### Font Assets
- `fonts/ShareTechMono-Regular.ttf` - Primary monospace font
- `fonts/VT323-Regular.ttf` - Display font for logo

---

## Performance Considerations

### Polling Intervals
- **Telemetry Worker**: 1 second (main loop)
- **CPU Metrics**: 0.1 second interval for accuracy
- **Cursor Blink**: 530ms interval
- **Clock Update**: 1 second interval

### Resource Management
- **QThread Architecture**: Non-blocking telemetry collection
- **Signal/Slot Communication**: Asynchronous data updates
- **Graceful Degradation**: Continue without optional features (NVML)
- **Explicit Cleanup**: NVML shutdown, thread termination on exit

---

## Current Test Bench

### Hardware Configuration
- **CPU**: AMD Ryzen 7 5700X
  - 8 Cores / 16 Threads
  - Zen 3 Architecture
  - 7nm Process
  - Base: 3.4 GHz, Boost: 4.6 GHz

- **GPU**: NVIDIA GeForce RTX 3060
  - 12GB GDDR6 VRAM
  - Ampere Architecture (GA106)
  - 3584 CUDA Cores
  - TDP: 170W

- **Platform**: Windows 10/11

---

## Version Information

- **Vitreos V3**: Pure Python PyQt6 architecture
- **PyQt6**: Latest stable (6.x)
- **Python**: 3.8+ (tested on 3.10+)
