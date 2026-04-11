# Product Overview

## Project Identity
**Vitreos V3 | System Sentinel** - "Intelligence through Transparency"

A high-end desktop hardware monitoring application for Windows built with pure Python and PyQt6. Features a custom frameless 'Liquid Glass' UI with real-time hardware telemetry, advanced NVIDIA sensor integration, and Figma-accurate design implementation.

## Value Proposition
Vitreos V3 provides absolute system transparency through comprehensive hardware monitoring with a professional-grade desktop interface. It combines aesthetic Figma-designed UI with deep system integration to deliver real-time monitoring for power users and system administrators.

## Core Capabilities

### Hardware Monitoring
- **CPU Monitor**: Real-time AMD Ryzen 7 5700X monitoring with per-core activity grid (8C/16T)
- **GPU Monitor**: Deep-level NVIDIA RTX 3060 metrics including clock speeds, power draw, VRAM utilization, and fan speeds via NVML
- **Thermal Control**: Comprehensive temperature monitoring across CPU, GPU, motherboard, and case sensors
- **Memory Array**: DDR4 RAM monitoring with slot-level visibility
- **Storage Array**: NVMe/SSD/HDD monitoring with health metrics
- **Network Interface**: Live bandwidth tracking and latency monitoring

### UI/UX Features
- **Liquid Glass Design**: Custom frameless window with transparent glass panels and neon accents
- **System Pulse Log**: Fixed 232px sidebar with scrolling terminal-style log and blinking cursor
- **2x3 Dashboard Grid**: Modular monitoring widgets in responsive grid layout
- **Segmented LED Bars**: Horizontal and vertical progress indicators with auto-alert coloring
- **Figma-Accurate**: Pixel-perfect implementation of design specifications

### Developer Tools
- **SQLite Logging**: Historical data storage for hardware metrics and events
- **QThread Architecture**: Non-blocking telemetry collection with signal/slot communication
- **Modular Design**: Separate modules for theme, widgets, telemetry, and monitoring components

## Target Users

### Primary Audience
- **Power Users**: Enthusiasts who demand deep system visibility and control
- **System Administrators**: IT professionals monitoring critical Windows systems
- **Content Creators**: Users running resource-intensive applications requiring thermal management
- **PC Builders**: Hardware enthusiasts with custom AMD/NVIDIA builds requiring monitoring

### Use Cases
1. **Real-time System Monitoring**: Continuous oversight of hardware health and performance
2. **Thermal Management**: Proactive temperature tracking to prevent thermal throttling
3. **Performance Tuning**: Monitor system behavior during overclocking and optimization
4. **Hardware Diagnostics**: Identify bottlenecks and hardware issues
5. **Development & Debugging**: Live system metrics during software development

## Technical Differentiators
- **Pure Python Architecture**: PyQt6-based desktop application with no web dependencies
- **Custom UI Framework**: Frameless 'Liquid Glass' design with transparent panels and neon accents
- **NVIDIA Deep Integration**: Direct NVML API access for professional-grade GPU monitoring
- **QThread Telemetry**: Non-blocking hardware collection at 1-second intervals
- **Figma Design System**: Complete theme engine with color palette, typography, and component library
- **Windows-Native**: Deep OS integration using psutil and pynvml for system-level access

## Current Test Bench
- **CPU**: AMD Ryzen 7 5700X (8C/16T, Zen 3, 7nm)
- **GPU**: NVIDIA GeForce RTX 3060 (12GB GDDR6)
- **Platform**: Windows 10/11
