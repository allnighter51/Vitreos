# Mercury PC Monitoring System - Pro Glass Edition

## 🚀 Overview

The Mercury PC Monitoring System has been completely transformed into a professional **Pro Glass** desktop application. This cutting-edge version features physics-based glass effects, advanced security monitoring, GPU deep-dive analytics, and enterprise-grade monitoring capabilities.

## ✨ Key Features

### 🎨 Liquid Glass Design
- **Physics-Based Glass**: `rgba(255, 255, 255, 0.05)` with `backdrop-filter: blur(16px) saturate(180%)`
- **Top-Left Bevel**: Pure white inner shadow at 10% opacity for light simulation
- **Professional Border**: 1px solid 'glass' edge using `rgba(255, 255, 255, 0.1)`
- **Floating Shadow**: Large, soft blur shadow with blue/purple tint (`#1a1a2e`)
- **Desktop Pro Aesthetic**: Clean, professional sans-serif typography

### 🛡️ Advanced Security Monitoring
- **USB Perimeter Guard**: Monitor USB device insertions/removals for security
- **Startup Sentinel**: Track Windows startup registry changes
- **Security Event Logging**: Real-time security event detection and logging
- **Threat Assessment**: Automatic severity classification (INFO/WARNING/CRITICAL)

### 🎮 GPU Deep-Dive Analytics
- **VRAM Saturation**: Monitor video RAM usage with pynvml integration
- **Fan Speed Tracking**: Real-time GPU fan speed monitoring
- **GPU Temperature**: Advanced GPU temperature tracking
- **GPU Usage**: Real-time GPU utilization monitoring
- **NVIDIA Management**: Full pynvml library integration for NVIDIA GPUs

### 🌐 Network Analytics
- **Ping Jitter Monitor**: Measure network stability and consistency
- **Bandwidth Hog Detection**: Identify processes consuming excessive bandwidth
- **Connection Analysis**: Advanced network connection monitoring
- **Performance Metrics**: Download/upload tracking with process attribution

### 🔮 Predictive Thermal Alert
- **Linear Regression Analysis**: Predict thermal throttling time
- **Proactive Alerts**: Warn before thermal events occur
- **Load Correlation**: Analyze temperature vs. CPU/GPU load patterns
- **Time-to-Throttle**: Display remaining time until thermal throttling

### ⚡ Advanced System Monitoring
- **Zombie Process Killer**: Automatically kill unresponsive processes
- **Power Consumption**: Estimate system power draw
- **Real-time Updates**: 2-second monitoring intervals
- **Status Indicators**: Professional health monitoring

### 🤖 Discord Remote Commands
- **Screenshot Capture**: Take desktop screenshots via Discord
- **Process Management**: Kill zombie processes remotely
- **System Testing**: Run diagnostic tests via Discord commands
- **Live Feedback**: Real-time Discord integration with advanced features

## 🚀 Quick Start

### Installation
```bash
# Install advanced requirements
pip install PyQt6 pynvml

# Or use the batch file
install_requirements.bat
```

### Launching the Application
```bash
# Launch the Pro Glass version
python mercury_pro_glass.py

# Or use the batch file
launch_pro_glass.bat
```

### Basic Usage
1. **Vitals Tab**: Monitor core system health with advanced GPU data
2. **Network Tab**: Analyze network performance and bandwidth usage
3. **Security Tab**: Enable USB and startup monitoring
4. **Console Tab**: Use advanced system controls and testing
5. **Logbook Tab**: View historical data and analytics

### Configuration
1. Go to **Console Tab** → **Webhook Testing**
2. Enter your Discord webhook URL
3. Click **Test Webhook** to verify functionality
4. Enable **Security Monitoring** for advanced protection

## 🎯 Professional Interface

### **Vitals Tab - Real-time System Health**
- **10 Advanced Monitoring Cards**: CPU/GPU temperature, usage, VRAM, fan speed, power draw
- **Predictive Thermal Analysis**: Time-to-throttle predictions
- **GPU Deep-Dive**: VRAM usage, fan speed, and utilization tracking
- **Power Estimation**: Real-time system power consumption

### **Network Tab - Connectivity & Traffic Analysis**
- **Ping & Jitter Monitoring**: Network stability analysis
- **Bandwidth Hogs Table**: Identify bandwidth-consuming processes
- **Download/Upload Tracking**: Real-time network usage
- **Connection Analysis**: Advanced network connection monitoring

### **Security Tab - PC Integrity Monitoring**
- **USB Device Monitoring**: Real-time USB insertion/removal alerts
- **Startup Registry Tracking**: Monitor startup program changes
- **Security Events Table**: Live security event logging
- **Threat Classification**: Automatic severity assessment

### **Console Tab - Active Control & Testing**
- **Zombie Process Killer**: Kill unresponsive processes
- **Webhook Testing**: Test Discord integration
- **Screenshot Capture**: Take desktop screenshots
- **Configuration Reset**: Reset all settings to defaults

### **Logbook Tab - Historical Data & Analytics**
- **Data Visualization**: Advanced historical data charts
- **Trend Analysis**: System performance over time
- **Event Correlation**: Security and performance event relationships

## 🔧 Technical Architecture

### Dependencies
- **PyQt6**: Professional desktop framework with transparency support
- **pynvml**: NVIDIA Management Library for advanced GPU monitoring
- **psutil**: System monitoring and statistics
- **requests**: Discord webhook integration
- **winreg**: Windows registry monitoring for security
- **subprocess**: System command execution for network analysis
- **statistics**: Mathematical analysis for predictive alerts

### Installation
```bash
# Required: PyQt6 for glass effects
pip install PyQt6

# Required: pynvml for GPU monitoring
pip install pynvml

# Optional: Enhanced monitoring (already included)
pip install psutil requests
```

### Configuration Files
- **mercury_config.json**: Professional configuration storage
- **Webhook URLs**: Securely stored with validation
- **Feature States**: Toggle states persist across sessions
- **Security Logs**: Persistent security event storage

### System Requirements
- **Windows 10/11** (primary support with full security features)
- **macOS/Linux** (with PyQt6 support, limited security features)
- **NVIDIA GPU** (required for pynvml GPU monitoring)
- **4GB RAM minimum** (8GB recommended)
- **Python 3.8+** (PyQt6 requirement)

## 🎨 Liquid Glass Physics

### **Surface Properties**
```css
background: rgba(255, 255, 255, 0.05)
backdrop-filter: blur(16px) saturate(180%)
```

### **Bevel Effects**
- **Top-Left Inner Shadow**: Pure white at 10% opacity
- **Light Simulation**: Creates 3D glass appearance
- **Depth Perception**: Professional layered effect

### **Border Styling**
```css
border: 1px solid rgba(255, 255, 255, 0.1)
border-radius: 16px
```

### **Floating Shadows**
- **Color**: Blue/purple tint (`#1a1a2e`)
- **Effect**: Large, soft blur for desktop floating appearance
- **Professional**: No black drop shadows, only subtle tints

## 🚨 Important Notes

### **PyQt6 & pynvml Requirements**
- **Essential**: PyQt6 is required for liquid glass effects
- **Essential**: pynvml is required for advanced GPU monitoring
- **Installation**: Run `install_requirements.bat` for complete setup
- **Compatibility**: Works with all modern operating systems

### **NVIDIA GPU Requirement**
- **Required**: pynvml library requires NVIDIA GPU for advanced features
- **Fallback**: System provides fallback values for non-NVIDIA systems
- **Detection**: Automatic GPU type detection and feature adaptation

### **Security Monitoring Limitations**
- **Windows Only**: Full USB and registry monitoring requires Windows
- **macOS/Linux**: Limited security features available
- **Permissions**: May require administrator privileges for registry access

### **Professional Desktop Focus**
- **No Mobile Elements**: Clean desktop-only interface
- **Professional Typography**: Sans-serif fonts with proper hierarchy
- **Glass Physics**: Realistic lighting and shadow effects
- **Desktop Integration**: Proper window management and controls

## 🔄 Migration from Previous Versions

### **Configuration Migration**
- **Existing mercury_config.json**: Automatically preserved
- **Webhook URLs**: Migrated with validation
- **Feature States**: Converted to new toggle system

### **Interface Changes**
- **Pro Glass replaces iOS**: Professional desktop aesthetic
- **Tab-based navigation**: Vitals, Network, Security, Console, Logbook
- **Advanced monitoring cards**: Information-focused design with real-time data
- **Professional controls**: Enhanced configuration interface

### **Technical Improvements**
- **PyQt6 Framework**: Professional desktop capabilities
- **pynvml Integration**: Advanced GPU monitoring
- **Security Monitoring**: USB and registry change detection
- **Predictive Analytics**: Thermal throttling prediction algorithms

## 🆕 What's New

### **Advanced Security Features**
- USB device insertion/removal monitoring
- Windows startup registry change detection
- Real-time security event logging with severity classification
- Threat assessment and alerting system

### **GPU Deep-Dive Analytics**
- VRAM usage monitoring with pynvml
- GPU fan speed tracking
- Advanced GPU temperature and utilization monitoring
- NVIDIA-specific hardware monitoring

### **Network Performance Analysis**
- Ping jitter measurement for gaming/Zoom stability
- Bandwidth hog identification by process
- Advanced network connection analysis
- Download/upload tracking with attribution

### **Predictive Thermal Management**
- Linear regression-based thermal prediction
- Proactive thermal throttling alerts
- Load vs. temperature correlation analysis
- Time-to-throttle countdown display

### **Professional System Controls**
- Zombie process detection and killing
- Advanced Discord integration with remote commands
- Screenshot capture functionality
- Configuration management and reset

### **Technical Excellence**
- PyQt6 framework for professional desktop effects
- pynvml library for enterprise GPU monitoring
- Multi-threaded security monitoring
- Advanced data visualization and analytics

## 📞 Professional Support

For issues, questions, or feature requests:
- **Installation**: Ensure PyQt6 and pynvml are properly installed
- **GPU Monitoring**: Verify NVIDIA GPU and drivers for pynvml features
- **Security Features**: Check Windows permissions for registry monitoring
- **Discord Integration**: Verify webhook URLs and network connectivity
- **Performance**: Monitor resource usage on lower-end systems

## 📄 License

© 2025 Mercury Systems
All rights reserved.

---

**Note**: This is a complete professional transformation of the Mercury PC Monitoring System. The Pro Glass edition provides enterprise-grade monitoring with cutting-edge desktop aesthetics, advanced security features, and comprehensive GPU analytics while maintaining all core functionality.
