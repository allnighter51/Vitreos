# 💎 Vitreos V3 | System Sentinel
**Intelligence through Transparency.**

Vitreos V3 is a high-end desktop hardware monitor and system sentinel for Windows. Built with pure Python and PyQt6, it features a custom frameless 'Liquid Glass' UI with real-time hardware telemetry, advanced NVIDIA sensor integration, and Figma-accurate design implementation.

## ✨ Core Features

* **CPU Monitor:** Real-time AMD Ryzen 7 5700X monitoring with per-core activity grid (8C/16T)
* **GPU Pro (NVIDIA NVML):** Deep-level NVIDIA RTX 3060 metrics including Clock Speeds, Power Draw (Watts), VRAM utilization, and Fan speeds
* **Thermal Control:** Comprehensive temperature monitoring across CPU, GPU, motherboard, and case sensors
* **Memory Array:** DDR4 RAM monitoring with slot-level visibility
* **Storage Array:** NVMe/SSD/HDD monitoring with health metrics
* **Network Interface:** Live bandwidth tracking and latency monitoring
* **System Pulse Log:** Fixed 232px sidebar with scrolling terminal-style log and blinking cursor
* **Liquid Glass UI:** Custom frameless window with transparent glass panels and neon accents

## 🛠️ Tech Stack
* **Desktop Framework:** PyQt6 (Pure Python)
* **Hardware APIs:** `psutil`, `nvidia-ml-py` (pynvml)
* **Database:** SQLite 3
* **Design System:** Figma-accurate color palette, typography, and component library
* **Fonts:** Share Tech Mono, VT323

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mercurycontentmgmt-svg/vitreos.git
   cd vitreos
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify NVIDIA drivers (optional, for GPU monitoring):**
   ```bash
   nvidia-smi
   ```

## 🎮 Launch Application

```bash
python vitreos_main_v3.py
```

**Architecture:**
- PyQt6 desktop application with frameless window
- QThread-based telemetry worker for non-blocking hardware collection
- Signal/slot architecture for asynchronous UI updates
- 1-second polling interval for real-time metrics

---

## 📦 Project Structure

```
Vitreos/
├── vitreos_main_v3.py      # Main application entry point
├── vitreos_theme.py        # Figma design system (colors, fonts, stylesheet)
├── vitreos_widgets.py      # Custom PyQt6 widgets (bars, frames, log)
├── vitreos_modules.py      # Dashboard monitoring modules (CPU, GPU, etc.)
├── vitreos_telemetry.py    # QThread hardware data collection
├── vitreos_db.py           # SQLite database module
├── config/                 # Configuration files
├── fonts/                  # Custom font assets
├── legacy_pyqt/            # Archived PyQt6 reference (READ-ONLY)
└── requirements.txt        # Python dependencies
```

---

## 🔧 Configuration Files

### **config/settings.json**
```json
{
  "discord": {
    "webhook_url": "",
    "message_id": ""
  },
  "monitoring": {
    "polling_interval_ms": 2000,
    "enable_gpu": true,
    "enable_security": true,
    "enable_network": true
  }
}
```

### **config/webhooks.json**
```json
{
  "channels": {
    "SECURITY": "",
    "THERMALS": "",
    "SYSTEM": "",
    "NETWORK": "",
    "STORAGE": ""
  },
  "default_webhook": "",
  "enable_alerts": true
}
```

---

## 🔒 Security Note
If you configure a Discord Webhook inside the app, it saves to `config/settings.json`. **Never commit these files to GitHub.** They are included in the `.gitignore` by default to protect your endpoints.

---

## 🐛 Troubleshooting

### **NVML Not Available**
- Install NVIDIA drivers
- Verify GPU is detected: `nvidia-smi`
- Install `nvidia-ml-py`: `pip install nvidia-ml-py`
- Application will continue without GPU monitoring if NVML unavailable

### **Fonts Not Loading**
- Ensure `fonts/` directory contains `ShareTechMono-Regular.ttf` and `VT323-Regular.ttf`
- Application will fallback to Consolas/Courier New if custom fonts unavailable

### **Application Won't Start**
- Verify Python 3.8+ is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Check for errors in console output

---

## 📊 Dashboard Layout

### 2x3 Grid
```
Row 1: [StorageArray] [CpuMonitor] [ThermalCtrl]
Row 2: [MemoryArray]  [GpuMonitor] [NetInterface]
```

### Sidebar (232px fixed width)
- VITREOS logo (VT323 font, 44pt)
- Status indicators (CPU, GPU, MEM, NET)
- Scrolling terminal log
- Blinking cursor prompt
- Bottom status bar with clock

---

## 🎨 Design System

### Color Palette
- **Primary:** Purple (#A855F7, #7C3AED, #6B3FA0)
- **Warning:** Orange (#FF6B00), Red (#FF4444)
- **Secondary:** Cyan (#06B6D4), Green (#22C55E)
- **Backgrounds:** Dark grays (#0D0D0D, #0A0A0A, #111111)
- **Borders:** Subtle grays (#2A2A2A, #1E1E1E, #1A1A1A)

### Typography
- **Monospace:** Share Tech Mono (primary), Consolas (fallback)
- **Display:** VT323 (primary), Courier New (fallback)
- **Scale:** 8 sizes from 44pt (logo) to 7pt (micro)

---

## 🖥️ Current Test Bench

- **CPU:** AMD Ryzen 7 5700X (8C/16T, Zen 3, 7nm)
- **GPU:** NVIDIA GeForce RTX 3060 (12GB GDDR6)
- **Platform:** Windows 10/11

---

## 📝 Development Guidelines

### Anti-Clutter Guardrails
1. **No Root Clutter:** Consolidate logic into existing modules
2. **No Redundancy:** Never create .backup, .old, or _v2 files
3. **Logic Preservation:** Treat `legacy_pyqt/` as read-only reference
4. **Zero One-Offs:** No temporary test scripts or fix-it batch files
5. **Automatic Cleanup:** Delete `__pycache__` after tasks

### Architecture Principles
- **QThread for Hardware:** Non-blocking telemetry collection
- **Signal/Slot Communication:** Asynchronous UI updates
- **Graceful Degradation:** Continue without optional features (NVML)
- **Figma-Accurate:** Exact pixel dimensions and color tokens

---

*Built for absolute system transparency.*
*v3.0.0 - Pure Python PyQt6 Architecture*
