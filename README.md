# 💎 Vitreos | System Sentinel

**Vitreos** is a high-performance, multi-threaded Windows monitoring suite designed for transparency and system integrity. Built with a "LiquidGlass" UI and powered by a dedicated asynchronous hardware engine, it provides real-time telemetry for gamers, power users, and tournament organizers.



---

## 🚀 Features

### **1. 10-Tab Command Center**
* **Vitals:** Real-time CPU/GPU/RAM core metrics.
* **GPU Pro:** Deep-dive NVIDIA telemetry (Clock speeds, Power Draw, Fan curves).
* **Processes:** Instant identification of top 10 memory-consuming applications.
* **Network:** Live upload/download bandwidth and ping tracking.
* **Storage:** Per-drive health, usage, and I/O R/W statistics.
* **Security:** Active monitoring for failed login events and unauthorized access.
* **Remote:** Discord Webhook integration for critical hardware alerts.

### **2. Performance Engine**
* **Asynchronous Threading:** All hardware polling (`psutil`, `pynvml`) runs on a dedicated **QThread** to ensure a 144Hz-smooth UI experience with zero "window freezing."
* **Defensive Architecture:** Built with strict type-safety and null-checks to prevent runtime crashes during hardware spikes.
* **UAC Admin Integration:** Native support for Windows Administrator privileges to access low-level GPU sensors.

### **3. Professional Desktop Integration**
* **System Tray:** Minimizes to the Windows tray with a custom context menu.
* **Frameless UI:** Modern, draggable custom header with "LiquidGlass" styling.
* **Zero-Footprint:** Lightweight background operation with a portable `.exe` runtime.

---

## 🛠️ Installation & Usage

### **The Compiled Experience (Recommended)**
Vitreos is distributed as a standalone, portable executable. No Python installation is required for end-users.
1. Download `Vitreos.exe` from the `dist/` folder.
2. Run as Administrator (required for GPU telemetry).

### **Development Runtime**
To run from source or modify the sentinel:
1. **Install Dependencies:**
   ```bat
   pip install PyQt6 psutil nvidia-ml-py Pillow requests pywin32
   ```
2. **Launch:**
   ```bat
   python src/main.py
   ```

---

## 📦 Build Instructions

To compile the application into a single `.exe` with the custom Vitreos icon:
```bat
pyinstaller --noconsole --onefile --uac-admin --clean --icon="logo.ico" --add-data "logo.ico;." --name="Vitreos" --collect-all "PyQt6" --hidden-import "pynvml" --hidden-import "psutil" src/main.py
```



---

## 📡 Remote Monitoring (Discord)

Vitreos supports "Heartbeat" updates. Configure your Webhook in the **Remote** tab or via `config/settings.json`:
* `webhook_url`: Your Discord Webhook URL.
* `alert_thresholds`: Custom temperature and usage triggers.

---

## 🛡️ Credits & Ownership
Developed as the official monitoring suite for **CCE (Tournament Hosting)**.
*"Intelligence through Transparency."*