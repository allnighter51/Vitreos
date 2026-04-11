# Development Guidelines

## Code Quality Standards

### Formatting Conventions
- **Indentation**: 4 spaces for Python
- **Line Length**: Flexible, prioritize readability over strict limits
- **String Quotes**: Double quotes for docstrings, single quotes for inline strings
- **Trailing Commas**: Not used in Python

### Structural Conventions
- **File Organization**: Group related functionality into modules
- **Import Order**: Standard library → Third-party → Local modules
- **Export Pattern**: Use `__all__` in modules for explicit public API
- **Component Structure**: Class-based with QObject inheritance for PyQt6 widgets

### Naming Standards
- **Python**: `snake_case` for functions/variables, `PascalCase` for classes
- **Constants**: `UPPER_SNAKE_CASE` for module-level constants
- **Private Members**: Prefix with underscore (e.g., `_internal_method`)
- **Type Aliases**: Descriptive names (e.g., `HardwareLogRow`)

### Documentation Standards
- **Python Docstrings**: Triple-quoted strings with description, Args, Returns sections
- **Module Headers**: Triple-quoted docstring at top of files describing purpose
- **Inline Comments**: Used sparingly, explain "why" not "what"

---

## Architectural Patterns

### QThread Architecture
**Pattern**: Separate thread for hardware monitoring to prevent UI blocking

**Implementation**:
```python
class TelemetryWorker(QThread):
    data_ready = pyqtSignal(dict)
    log_message = pyqtSignal(str, str, str)
    
    def run(self):
        while self.running:
            data = self._collect_telemetry()
            self.data_ready.emit(data)
            time.sleep(1.0)

# Main window connects signals
self.telemetry_worker.data_ready.connect(self._update_modules)
self.telemetry_worker.log_message.connect(self._handle_log)
```

**Rationale**: Non-blocking hardware collection, responsive UI

**Frequency**: 5/5 files use QThread pattern

---

### Signal/Slot Communication
**Pattern**: PyQt6 signals for asynchronous communication between threads

**Implementation**:
```python
class DatabaseWorker(QObject):
    log_entry_requested = pyqtSignal(dict)
    
    @pyqtSlot(dict)
    def write_log_entry(self, stats_dict: Dict[str, Any]) -> None:
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO hardware_log ...")
        self.connection.commit()

# Main thread emits signal
self.db_worker.log_entry_requested.emit(stats_dict)
```

**Frequency**: 4/5 files use signal/slot pattern

---

### Class-Based Widgets
**Pattern**: Encapsulate widget functionality in dedicated classes

**Examples**:
```python
class VitreosSegmentedBar(QWidget):
    def __init__(self, segments: int = 22, height: int = 6):
        super().__init__()
        self.segments = segments
        self.value = 0.0
    
    def set_value(self, value: float, max_value: float = 100.0) -> None:
        self.value = min(value, max_value)
        self.update()
    
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        # Custom painting logic

class CpuMonitor(VitreosWinFrame):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="CPU_MONITOR", accent_color="cyan")
        self._setup_content()
    
    def update_data(self, data: Dict[str, Any]) -> None:
        # Update UI with fresh data
```

**Rationale**: Encapsulation, reusability, clear separation of concerns

**Frequency**: 5/5 files use class-based organization

---

### Graceful Degradation
**Pattern**: Check for optional dependencies, provide fallback behavior

**Implementation**:
```python
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    print("[TELEMETRY] pynvml not available - GPU monitoring disabled")

def _get_gpu_data(self) -> Dict[str, Any]:
    if not self.nvml_initialized:
        return {
            'usage': 0, 'vram': 0, 'temp': 0,
            'coreClock': 0, 'memClock': 0, 'power': 0
        }
    # Real implementation
```

**Frequency**: 4/5 files implement graceful degradation

---

### Theme System
**Pattern**: Centralized design tokens with helper functions

**Implementation**:
```python
VITREOS_COLORS: Dict[str, str] = {
    'primary_purple': '#A855F7',
    'warning_orange': '#FF6B00',
    'bg_primary': '#0D0D0D',
    # ... 30+ colors
}

def get_color(color_name: str, alpha: int = 255) -> QColor:
    hex_color = VITREOS_COLORS.get(color_name, '#FFFFFF')
    return hex_to_qcolor(hex_color, alpha)

def get_font(font_type: str = 'mono', size: int = 10) -> QFont:
    primary = VITREOS_FONTS['mono']
    fallback = VITREOS_FONTS['fallback_mono']
    font = QFont(primary, size)
    return font
```

**Frequency**: 5/5 files use theme system

---

### Custom Paint Events
**Pattern**: Override paintEvent for custom widget rendering

**Implementation**:
```python
def paintEvent(self, event: QPaintEvent) -> None:
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Calculate dimensions
    width = self.width()
    segment_width = (width - (self.segments - 1) * self.gap) / self.segments
    
    # Draw segments
    for i in range(self.segments):
        x = i * (segment_width + self.gap)
        rect = QRectF(x, 0, segment_width, self.bar_height)
        
        if i < filled_segments:
            painter.fillRect(rect, get_color('primary_purple'))
        else:
            painter.fillRect(rect, get_color('segment_off'))
```

**Frequency**: 3/5 files use custom painting

---

## Common Code Idioms

### Try-Except with Logging
**Pattern**: Wrap risky operations in try-except, log errors

```python
try:
    utilization = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
    temp = pynvml.nvmlDeviceGetTemperature(self.gpu_handle, 0)
except Exception as e:
    self.log_message.emit("WARN", f"GPU data error: {e}", "warning_orange")
    return {'usage': 0, 'temp': 0}
```

**Frequency**: 5/5 files use this pattern extensively

---

### Type Hints and TypedDict
**Pattern**: Use type hints for function signatures, TypedDict for structured data

```python
from typing import Dict, Any, Optional, List, TypedDict

class HardwareLogRow(TypedDict):
    timestamp: str
    cpu_temp: float
    gpu_temp: float

def _get_cpu_data(self) -> Dict[str, Any]:
    return {
        'totalLoad': cpu_percent,
        'temp': cpu_temp,
        'cores': per_cpu
    }

def update_data(self, data: Dict[str, Any]) -> None:
    total_load = data.get('totalLoad', 0)
    self.load_bar.set_value(total_load, 100)
```

**Frequency**: 5/5 files use comprehensive type hints

---

### QTimer for Periodic Updates
**Pattern**: Use QTimer for UI animations and periodic updates

```python
def _start_timers(self) -> None:
    # Cursor blink
    self.cursor_timer = QTimer(self)
    self.cursor_timer.timeout.connect(self._toggle_cursor)
    self.cursor_timer.start(530)
    
    # Clock update
    self.clock_timer = QTimer(self)
    self.clock_timer.timeout.connect(self._update_clock)
    self.clock_timer.start(1000)

def _toggle_cursor(self) -> None:
    self.cursor_visible = not self.cursor_visible
    self.cursor_label.setVisible(self.cursor_visible)
```

**Frequency**: 3/5 files use QTimer

---

### Frameless Window Drag Support
**Pattern**: Implement mouse events for dragging frameless windows

```python
def mousePressEvent(self, event: QMouseEvent) -> None:
    if event.button() == Qt.MouseButton.LeftButton:
        self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        event.accept()

def mouseMoveEvent(self, event: QMouseEvent) -> None:
    if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
        self.move(event.globalPosition().toPoint() - self.drag_position)
        event.accept()

def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    self.drag_position = None
```

**Frequency**: 2/5 files implement drag support

---

## Internal API Usage Patterns

### NVML GPU Monitoring
**Pattern**: Initialize NVML, get device handle, query metrics, cleanup

```python
# Initialization
pynvml.nvmlInit()
gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)

# Query metrics
utilization = pynvml.nvmlDeviceGetUtilizationRates(gpu_handle)
memory_info = pynvml.nvmlDeviceGetMemoryInfo(gpu_handle)
temp = pynvml.nvmlDeviceGetTemperature(gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
power = pynvml.nvmlDeviceGetPowerUsage(gpu_handle) / 1000  # Convert to watts
core_clock = pynvml.nvmlDeviceGetClockInfo(gpu_handle, pynvml.NVML_CLOCK_GRAPHICS)
mem_clock = pynvml.nvmlDeviceGetClockInfo(gpu_handle, pynvml.NVML_CLOCK_MEM)
fan_speed = pynvml.nvmlDeviceGetFanSpeed(gpu_handle)

# Cleanup
pynvml.nvmlShutdown()
```

**Frequency**: 2/5 files interact with NVML

---

### psutil System Monitoring
**Pattern**: Direct function calls for system metrics

```python
cpu_percent = psutil.cpu_percent(interval=0.1)
cpu_freq = psutil.cpu_freq()
per_cpu = psutil.cpu_percent(percpu=True)
mem = psutil.virtual_memory()
net_io = psutil.net_io_counters()
disk_usage = psutil.disk_usage(partition.mountpoint)
temps = psutil.sensors_temperatures()
fans = psutil.sensors_fans()
```

**Frequency**: 5/5 files use psutil

---

### SQLite with QThread Worker
**Pattern**: Use dedicated worker thread for database operations

```python
class DatabaseWorker(QObject):
    log_entry_requested = pyqtSignal(dict)
    
    def __init__(self, db_connection: sqlite3.Connection):
        super().__init__()
        self.connection = db_connection
    
    @pyqtSlot(dict)
    def write_log_entry(self, stats_dict: Dict[str, Any]) -> None:
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO hardware_log ...")
        self.connection.commit()

# Main thread setup
self.connection = sqlite3.connect(db_path, check_same_thread=False)
self.db_thread = QThread()
self.db_worker = DatabaseWorker(self.connection)
self.db_worker.moveToThread(self.db_thread)
self.db_thread.start()
```

**Frequency**: 2/5 files use database pattern

---

### PyQt6 Stylesheets (QSS)
**Pattern**: Use inline stylesheets for dynamic styling

```python
self.setStyleSheet(f"""
    VitreosWinFrame {{
        background: {VITREOS_COLORS['bg_primary']};
        border: 1px solid {VITREOS_COLORS['border_primary']};
    }}
    #TitleBar {{
        background: {VITREOS_COLORS['bg_titlebar']};
        border-bottom: 1px solid {VITREOS_COLORS['border_primary']};
    }}
""")

# Dynamic styling
if temp > 85:
    self.temp_value_label.setStyleSheet(f"color: {VITREOS_COLORS['critical_red']};")
else:
    self.temp_value_label.setStyleSheet(f"color: {VITREOS_COLORS['cyan']};")
```

**Frequency**: 5/5 files use QSS styling

---

## Popular Annotations

### Python Type Hints
```python
from typing import Dict, Any, List, Tuple, Optional

def collect_all(self) -> Dict[str, Any]:
    pass

def get_all_process_rules(self) -> Dict[str, Tuple[str, str]]:
    pass

def update_data(self, data: Dict[str, Any]) -> None:
    pass
```

**Frequency**: 5/5 Python files use type hints

---

### PyQt6 Decorators
```python
from PyQt6.QtCore import pyqtSignal, pyqtSlot

class DatabaseWorker(QObject):
    log_entry_requested = pyqtSignal(dict)
    
    @pyqtSlot(dict)
    def write_log_entry(self, stats_dict: Dict[str, Any]) -> None:
        pass
```

**Frequency**: 3/5 files use PyQt6 decorators

---

## Project-Specific Practices

### Logging with Prefixes
**Pattern**: Use `[VITREOS]` or `[TELEMETRY]` prefix for all log messages

```python
print("[VITREOS] Main window initialized")
print("[VITREOS THEME] Loaded font: Share Tech Mono")
print("[TELEMETRY] pynvml not available - GPU monitoring disabled")
self.log_message.emit("OK", "NVML initialized - GPU monitoring active", "green")
```

**Rationale**: Easy identification of log source

**Frequency**: 5/5 files use prefixed logging

---

### Placeholder Values for Unavailable Metrics
**Pattern**: Return sensible defaults when hardware data unavailable

```python
return {
    'packagePwr': 142,  # Placeholder - requires specific hardware access
    'vid': 1.31,  # Placeholder
    'memBandwidth': 756,  # Placeholder - requires calculation
}
```

**Frequency**: 4/5 files use placeholder pattern

---

### Cleanup Methods
**Pattern**: Provide explicit cleanup methods for resource management

```python
def stop(self) -> None:
    """Stop the telemetry worker gracefully."""
    self.running = False
    if self.nvml_initialized:
        try:
            pynvml.nvmlShutdown()
        except:
            pass

def closeEvent(self, event) -> None:
    """Clean shutdown of telemetry worker."""
    if self.telemetry_worker:
        self.telemetry_worker.stop()
        self.telemetry_worker.wait(2000)
    event.accept()
```

**Frequency**: 5/5 files implement cleanup methods

---

### Figma-Accurate Dimensions
**Pattern**: Use exact pixel dimensions from Figma specifications

```python
self.setFixedWidth(232)  # Sidebar width
title_bar.setFixedHeight(24)  # Title bar height
bottom_bar.setFixedHeight(20)  # Status bar height
dot.setFixedSize(6, 6)  # Indicator dot
min_btn.setFixedSize(14, 14)  # Window control button
```

**Frequency**: 4/5 files use exact dimensions

---

### Alert Zone Coloring
**Pattern**: Auto-change colors when metrics exceed thresholds

```python
# Determine if in alert zone
alert_zone = filled_segments >= int(self.segments * self.alert_threshold)

if alert_zone:
    color = get_color('warning_orange')
else:
    color = get_color(self.color_name)

# Temperature alert
if temp > 85:
    self.temp_value_label.setStyleSheet(f"color: {VITREOS_COLORS['critical_red']};")
```

**Frequency**: 4/5 files implement alert coloring

---

## Anti-Patterns to Avoid

### No Root Clutter
- Never create temporary files in project root
- Consolidate logic into existing modules
- No `.backup`, `.old`, or `_v2` files

### No Redundancy
- Edit source of truth directly
- No duplicate implementations
- Treat `legacy_pyqt/` as read-only reference

### No One-Off Scripts
- No temporary test scripts
- No fix-it batch files
- Run tests in terminal or temporary code blocks

### Automatic Cleanup
- Delete `__pycache__` after tasks
- Remove build artifacts immediately
- Keep workspace clean

---

## Testing Practices

### Manual Testing
- Run application: `python vitreos_main_v3.py`
- Verify NVML availability: `nvidia-smi`
- Check font loading in console output

### Error Handling
- Always wrap hardware API calls in try-except
- Log errors with context
- Provide fallback values for missing data

### Validation
- Verify configuration files exist before loading
- Check optional dependencies before use
- Validate data types in update methods

---

## Performance Considerations

### Polling Intervals
- Telemetry worker: 1 second
- CPU metrics: 0.1 second interval for accuracy
- Cursor blink: 530ms
- Clock update: 1 second

### Resource Management
- Use `check_same_thread=False` for SQLite in multi-threaded contexts
- Run telemetry in separate QThread
- Close connections explicitly in cleanup methods

### UI Responsiveness
- Never block UI thread with hardware queries
- Use signals/slots for asynchronous updates
- Minimize paintEvent complexity
