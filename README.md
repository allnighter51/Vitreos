# 💎 Vitreos | System Sentinel
**Intelligence through Transparency.**

Vitreos (Architect Edition) is a high-end, PyQt6-based desktop hardware monitor and system sentinel for Windows. It features a custom frameless 'Liquid Glass' UI, asynchronous hardware polling, advanced NVIDIA sensor integration, and remote Discord webhook alerting.

## ✨ Core Features

* **Vitals & Hardware:** Real-time monitoring of CPU, RAM, Disk, and predictive thermal tracking.
* **GPU Pro (NVIDIA NVML):** Deep-level access to NVIDIA GPU metrics including Clock Speeds, Power Draw (Watts), VRAM utilization, and Fan speeds.
* **Network & Bandwidth:** Live Ping/Jitter tracking and dynamic identification of network bandwidth hogs.
* **Security & Integrity:** Active monitoring of USB insertion/removal and unapproved Windows Startup registry modifications.
* **Remote Dispatch:** Headless alerting via Discord Webhooks for critical thresholds (Temp >85°C, CPU >95%, Disk >95%).
* **Live Console:** An integrated CMD-style terminal bridging hardware thread logs directly to the UI for live debugging.

## 🛠️ Tech Stack
* **Framework:** Python 3.x, PyQt6
* **Hardware APIs:** `psutil`, `nvidia-ml-py` (pynvml)
* **OS Integration:** `winreg`, `ctypes`, `subprocess`

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/mercurycontentmgmt-svg/vitreos.git](https://github.com/mercurycontentmgmt-svg/vitreos.git)
   cd vitreos
   ```

2. **Install dependencies:**
   Ensure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run in Development Mode:**
   ```bash
   python vitreos_main.py
   ```

## 📦 Building the Executable (V1.0)
To compile Vitreos into a standalone `.exe` for distribution, we use PyInstaller. Run the following command from the root directory to embed the icon and request necessary Administrator privileges for hardware sensors:

```bash
pyinstaller --noconsole --onefile --uac-admin --clean --icon="logo.ico" --add-data "logo.ico;." --name="Vitreos_Sentinel_v1" vitreos_main.py
```
*The compiled executable will be located in the `dist/` folder.*

## 🔒 Security Note
If you configure a Discord Webhook inside the app, it saves to a local `mercury_config.json` file. **Never commit this file to GitHub.** It is included in the `.gitignore` by default to protect your endpoints.

---
*Built for absolute system transparency.*
```