# 💎 Vitreos | System Sentinel
> **Total Transparency. Absolute Control.**

Vitreos is a comprehensive monitoring suite that provides real-time oversight of every critical component in your system. By aggregating telemetry from dozens of hardware sensors, network adapters, and system processes, it offers a "single pane of glass" view into the health and performance of your machine.

## 🕹️ The 10 Core Intelligence Modules

Vitreos is divided into ten specialized tabs, each providing a deep dive into a specific facet of your system’s operation:

### 1. VITALS (The Central Command)
The heartbeat of the application. The Vitals module features a real-time activity grid that monitors every CPU core individually. It provides high-frequency updates on package temperature, total load, and voltage (VID), ensuring you can spot thermal throttling or core-parking issues instantly.

### 2. NETWORK (Bandwidth Intelligence)
A sophisticated traffic analyzer. This module allows you to select specific network adapters and monitor live throughput. It tracks download and upload speeds with high-fidelity waveforms, identifies latency spikes, and records network peaks to help diagnose ISP inconsistencies or local congestion.

### 3. PROCESSES (Resource Attribution)
A specialized task manager designed for resource auditing. It tracks every active application, ranking them by CPU and Memory consumption. This allows you to identify "zombie" processes or background tasks that are siphoning performance during critical workloads.

### 4. GPU PRO (Advanced Graphics Metrics)
Engineered for high-end graphics workstations. Beyond basic temperature, GPU Pro monitors VRAM allocation at the chip level, core and memory clock frequencies, and real-time power draw in Watts. It includes a dedicated "Fan Row" to audit the RPM of every individual cooling fan on the card.

### 5. SECURITY (Event Surveillance)
The security module acts as a watchdog for your system. It integrates with Discord webhooks to send automated alerts when specific thresholds are breached—such as unauthorized access attempts, critical thermal levels, or suspicious network activity.

### 6. STORAGE (Disk Health & Arrays)
Complete oversight of your data integrity. Storage monitors NVMe, SSD, and HDD health metrics, including remaining life percentages, read/write speeds, and capacity thresholds. It is designed to alert you to imminent drive failure before data loss occurs.

### 7. TWEAKS (Performance Optimization)
The operational control center for system behavior. This module provides toggles for performance profiles, allowing you to adjust how the system prioritizes resources. It includes advanced controls for background services and OS-level optimizations.

### 8. CONSOLE (Raw Telemetry Stream)
For the developer and data scientist. The Console provides a raw, unfiltered stream of every telemetry poll captured by the system. It is invaluable for debugging hardware-software conflicts or performing a forensic audit of system performance over time.

### 9. REMOTE (Integration & Presence)
Connect Vitreos to your digital workflow. This module manages external integrations, including Discord Rich Presence, which can broadcast your hardware stats to your profile. It also handles the configuration for remote telemetry access.

### 10. SETTINGS (Global Configuration)
The fine-tuning hub for the Sentinel itself. Adjust polling intervals (down to 100ms for ultra-high resolution), manage your alert webhooks, and toggle module-specific features like "Verbose Mode" for deep logging.

---

## 🚀 Installation & Setup Guide

Vitreos requires a specific environment to ensure high-frequency polling and UI fluidity. Follow this guide to initialize the Sentinel on your system.

### 1. Environment Preparation
Ensure you have the latest stable environment installed on your machine. Vitreos is optimized for 64-bit architectures on Windows 10 and 11.

### 2. Repository Initialization
Clone the Sentinel assets to your local directory:
```bash
git clone https://github.com/mercurycontentmgmt-svg/vitreos.git
cd vitreos
```

### 3. Dependency Deployment
Deploy the necessary libraries required for hardware sensor communication:
```bash
pip install -r requirements.txt
```

### 4. Asset Integration (Fonts)
For the interface to render correctly, you must install the custom identity fonts located in the `fonts/` directory:
1. Open the `fonts/` folder.
2. Right-click `ShareTechMono-Regular.ttf` and select **Install**.
3. Right-click `VT323-Regular.ttf` and select **Install**.

### 5. Graphics Driver Verification
If you are using the **GPU PRO** module, ensure your graphics drivers are up to date. You can verify your hardware's readiness by running:
```bash
nvidia-smi
```

---

## 🔧 Post-Install Configuration

Before the first launch, configure your operational parameters in `config/settings.json`:

1. **Polling Intervals:** Set `polling_interval_ms` to `1000` for standard use or `200` for high-performance auditing.
2. **Alerts:** Add your Discord Webhook URL to the `discord` section to enable the **Security** module's alert capabilities.
3. **Module Toggle:** Enable or disable specific modules (GPU, Network, Security) based on your hardware availability.

## 🎮 Launching the Sentinel

Once configured, launch the main execution script:
```bash
python vitreos_main_v3.py
```

---

## 🐛 Troubleshooting

* **UI Elements Oversized:** Ensure your Windows Display Scaling is set to 100%. Vitreos is pixel-perfect and may distort at high scaling percentages.
* **Missing GPU Data:** Verify that the `nvidia-ml` library is correctly installed and that you are using a compatible hardware driver.
* **Log Freeze:** If the System Pulse Log stops scrolling, check the **Console** tab for "Poll Failures," which may indicate a sensor conflict.

*Built for absolute system transparency.*
*v3.0.0 — Stable Build*