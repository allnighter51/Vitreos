# Vitreos V3: Development & Behavioral Guardrails

## 1. Core Philosophical Directive

### Surgical Precision
**Touch only the code necessary for the current task. No "improving" adjacent formatting.**

- Make targeted edits to specific functions/methods
- Do not refactor unrelated code in the same file
- Preserve existing formatting and style unless explicitly requested
- No "while we're here" improvements

### Simplicity Over Speculation
**No "future-proofing" or extra configurations. If it's for a single-use logic (like a specific GPU threshold for the 3060), keep it direct.**

- Hardcode values when appropriate (e.g., RTX 3060 VRAM: 12GB)
- No abstract configuration systems for single-use cases
- Direct implementation over flexible architecture
- Example: `if vram_total == 12:` not `if vram_total == config.get('gpu_vram_max')`

### No Root Clutter
**Do not create new files in the root. Consolidate logic into vitreos_main_v3.py, vitreos_theme.py, vitreos_widgets.py, and vitreos_telemetry.py.**

- All new functionality goes into existing V3 modules
- No temporary test files in root
- No utility scripts or helpers in root
- Use existing module structure:
  - `vitreos_main_v3.py` - Application logic and window management
  - `vitreos_theme.py` - Design tokens and styling
  - `vitreos_widgets.py` - Custom UI components
  - `vitreos_modules.py` - Dashboard monitoring widgets
  - `vitreos_telemetry.py` - Hardware data collection
  - `vitreos_db.py` - Database operations

---

## 2. Pre-Execution Protocol

### State Assumptions
**Before coding, name the hardware (currently RTX 3060 / Ryzen 5700X) and the UI target (Figma Liquid Glass).**

**Current Hardware Configuration:**
- **CPU:** AMD Ryzen 7 5700X (8C/16T, Zen 3, 7nm)
- **GPU:** NVIDIA GeForce RTX 3060 (12GB GDDR6)
- **Platform:** Windows 10/11

**UI Target:**
- **Design System:** Figma Liquid Glass
- **Sidebar Width:** 232px (fixed)
- **Title Bar Height:** 24px
- **Grid Layout:** 2x3 dashboard
- **Color Palette:** Purple (#A855F7), Orange (#FF6B00), Cyan (#06B6D4)
- **Fonts:** Share Tech Mono (mono), VT323 (display)

**Pre-Code Checklist:**
1. Confirm hardware target (RTX 3060 / Ryzen 5700X)
2. Confirm UI specifications from Figma
3. Identify target module for changes
4. State expected behavior after changes

### Propose Simplification
**If a task looks like it will take 100+ lines, offer a 20-line alternative first.**

**Simplification Strategy:**
1. Identify the core requirement
2. Propose minimal implementation
3. Ask: "Do we need the full solution or will this work?"
4. Only implement complex solution if user confirms necessity

**Example:**
```
User: "Add GPU overclocking controls with voltage curves and frequency tables"

Response: "I can implement this two ways:
1. Simple: Add +/- buttons for core/mem offset (20 lines)
2. Complex: Full curve editor with voltage control (200+ lines)

For RTX 3060 monitoring, option 1 covers 90% of use cases. Proceed with simple version?"
```

---

## 3. Logic & UI Fidelity

### Figma is the Law
**Every UI change must map directly to the hex codes, 2px gaps, and 232px sidebar width defined in the Figma inventory.**

**Figma Specifications (Non-Negotiable):**

**Dimensions:**
- Sidebar width: `232px` (fixed)
- Title bar height: `24px`
- Bottom bar height: `20px`
- Indicator dot size: `6x6px`
- Window control buttons: `14x14px`
- Grid gap: `8px`
- Segment gap: `2px`

**Colors (from VITREOS_COLORS):**
- Primary purple: `#A855F7`
- Purple glow: `#7C3AED`
- Warning orange: `#FF6B00`
- Critical red: `#FF4444`
- Cyan: `#06B6D4`
- Green: `#22C55E`
- Background primary: `#0D0D0D`
- Border primary: `#2A2A2A`

**Typography:**
- Logo: VT323, 44pt
- Title: Share Tech Mono, 14pt
- Value large: Share Tech Mono, 13pt
- Value medium: Share Tech Mono, 11pt
- Label: Share Tech Mono, 10pt
- Small: Share Tech Mono, 9pt
- Tiny: Share Tech Mono, 8pt
- Micro: Share Tech Mono, 7pt

**Verification Process:**
1. Check hex codes match VITREOS_COLORS exactly
2. Verify pixel dimensions match Figma specs
3. Confirm font sizes use FONT_SIZES constants
4. Test visual output against Figma mockup

### Legacy Brain Reclaim
**Use legacy_pyqt/ as a read-only logic source. Refactor the 10 core modules (Security, Network, etc.) into the V3 grid without duplicating files.**

**Legacy Modules to Reclaim:**
1. `tab_vitals.py` - CPU/RAM/Disk monitoring
2. `tab_gpu_pro.py` - Advanced GPU controls
3. `tab_network.py` - Network analytics
4. `tab_security.py` - Security surveillance
5. `tab_storage.py` - Disk management
6. `tab_processes.py` - Process monitoring
7. `tab_console.py` - Live terminal
8. `tab_logbook.py` - Event logging
9. `tab_remote.py` - Discord webhook configuration
10. `tab_settings.py` - Application settings

**Reclamation Process:**
1. Read logic from `legacy_pyqt/tabs/tab_*.py`
2. Extract core functionality (data collection, calculations)
3. Adapt to V3 architecture (QThread signals, Figma widgets)
4. Implement in `vitreos_modules.py` as new dashboard widget
5. **Never duplicate files** - refactor into V3 structure

**Example:**
```python
# DON'T: Copy legacy_pyqt/tabs/tab_security.py to root
# DO: Extract logic and create SecurityMonitor in vitreos_modules.py

class SecurityMonitor(VitreosWinFrame):
    """Security monitoring widget - logic from legacy tab_security.py"""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(title="SECURITY_MONITOR", accent_color="critical_red")
        # Refactored logic here
```

---

## 4. Goal-Driven Verification

### The Loop
**Define the check (e.g., "Verify RTX 3060 VRAM percentage updates in the SegmentedBar") and loop until the user confirms the visual result.**

**Verification Protocol:**
1. **State the Goal:** "I will verify that GPU VRAM usage updates the orange segmented bar in real-time"
2. **Implement Changes:** Make targeted code modifications
3. **Define Test:** "Run `python vitreos_main_v3.py` and observe GPU VRAM bar"
4. **Request Confirmation:** "Does the VRAM bar update every second and turn orange above 80%?"
5. **Loop if Needed:** If user reports issue, diagnose and iterate
6. **Confirm Success:** User explicitly confirms visual behavior

**Example Verification Loop:**
```
Agent: "I've updated GpuMonitor to display RTX 3060 VRAM (12GB max). 
        The bar should show current usage and turn orange above 9.6GB.
        Please run the app and confirm the VRAM bar updates correctly."

User: "The bar updates but stays purple even at 95%"

Agent: "I see the issue - alert_threshold not applied to VRAM bar.
        Fixing now..."

[Makes targeted fix]

Agent: "Updated. The VRAM bar should now turn orange above 80% (9.6GB).
        Please verify the color change occurs."

User: "Confirmed - works perfectly"

Agent: "Verification complete. Cleaning up artifacts..."
```

### The Clean Exit
**Automatically delete __pycache__ and any temp artifacts immediately after verification.**

**Cleanup Checklist:**
1. Delete `__pycache__/` directories
2. Delete `.pyc` files
3. Delete any temporary test files
4. Delete build artifacts
5. Confirm clean workspace

**Automatic Cleanup Command:**
```bash
# After successful verification
rmdir /s /q __pycache__ 2>nul
del /s /q *.pyc 2>nul
echo Workspace cleaned
```

**When to Clean:**
- After successful verification
- After completing a feature
- Before committing changes
- When switching tasks

---

## 5. Communication Standards

### Before Making Changes
- State hardware target (RTX 3060 / Ryzen 5700X)
- Identify target module(s)
- Propose simplest solution first
- Confirm approach with user

### During Implementation
- Make surgical edits only
- Preserve existing code structure
- Use Figma specifications exactly
- No speculative improvements

### After Implementation
- Define verification test
- Request user confirmation
- Loop until success
- Clean up artifacts automatically

---

## 6. Anti-Patterns (Forbidden Actions)

### ❌ Never Do This:
- Create new files in root directory
- Duplicate code from `legacy_pyqt/`
- Add "future-proof" configuration systems
- Refactor unrelated code
- Improve formatting "while we're here"
- Add features not explicitly requested
- Create abstract base classes for single use
- Add logging frameworks for simple prints
- Create utility modules for one-off functions

### ✅ Always Do This:
- Edit existing V3 modules only
- Extract logic from `legacy_pyqt/` and refactor
- Hardcode values when appropriate
- Make targeted surgical edits
- Preserve existing formatting
- Implement only requested features
- Use direct implementations
- Use simple print statements
- Inline helper functions when small

---

## 7. Hardware-Specific Guidelines

### RTX 3060 Specifications
- **VRAM:** 12GB GDDR6 (hardcode, no config)
- **TDP:** 170W nominal
- **Thermal Limit:** 83°C (NVIDIA spec)
- **Alert Threshold:** 85°C (user preference)
- **Boost Clock:** ~1777 MHz (varies by model)

### Ryzen 7 5700X Specifications
- **Cores:** 8C/16T (hardcode, no detection)
- **TDP:** 65W
- **Max Temp:** 90°C (AMD spec)
- **Alert Threshold:** 85°C (user preference)
- **Base Clock:** 3.4 GHz
- **Boost Clock:** 4.6 GHz

**Implementation Example:**
```python
# GOOD: Direct implementation for known hardware
if temp > 85:
    self.temp_label.setStyleSheet(f"color: {VITREOS_COLORS['critical_red']};")

# BAD: Over-engineered for single hardware config
alert_temp = self.config.get('gpu_alert_threshold', 85)
if temp > alert_temp:
    color = self.config.get('alert_color', 'critical_red')
    self.temp_label.setStyleSheet(f"color: {VITREOS_COLORS[color]};")
```

---

## 8. Module Responsibility Matrix

| Module | Responsibility | What Goes Here |
|--------|---------------|----------------|
| `vitreos_main_v3.py` | Application entry, window management, layout | Main window class, grid setup, signal routing |
| `vitreos_theme.py` | Design tokens, colors, fonts, global styles | VITREOS_COLORS, FONT_SIZES, QSS stylesheets |
| `vitreos_widgets.py` | Reusable UI components | SegmentedBar, VerticalBar, WinFrame, SystemPulseLog |
| `vitreos_modules.py` | Dashboard monitoring widgets | CpuMonitor, GpuMonitor, ThermalCtrl, etc. |
| `vitreos_telemetry.py` | Hardware data collection | TelemetryWorker, psutil/pynvml calls |
| `vitreos_db.py` | Database operations | SQLite connection, logging, queries |
| `config/` | Settings and webhooks | JSON configuration files and loaders |

**Decision Tree:**
- Adding new color? → `vitreos_theme.py`
- Adding new widget type? → `vitreos_widgets.py`
- Adding new dashboard panel? → `vitreos_modules.py`
- Adding new hardware metric? → `vitreos_telemetry.py`
- Adding new database table? → `vitreos_db.py`
- Changing window layout? → `vitreos_main_v3.py`

---

## 9. Verification Examples

### Example 1: GPU VRAM Bar
**Goal:** Verify RTX 3060 VRAM usage displays correctly

**Test:**
1. Run `python vitreos_main_v3.py`
2. Observe GPU VRAM bar in GpuMonitor widget
3. Confirm value shows "X.X / 12.0 GB"
4. Confirm bar fills proportionally
5. Confirm bar turns orange above 9.6GB (80%)

**Success Criteria:**
- ✓ VRAM value updates every second
- ✓ Bar fills from 0-100% based on usage
- ✓ Color changes to orange above 80%
- ✓ No console errors

### Example 2: CPU Core Grid
**Goal:** Verify Ryzen 5700X per-core activity displays correctly

**Test:**
1. Run `python vitreos_main_v3.py`
2. Observe CPU core grid in CpuMonitor widget
3. Confirm 16 vertical bars (8C/16T)
4. Confirm bars update independently
5. Confirm bars turn orange above 75%

**Success Criteria:**
- ✓ 16 vertical bars visible (4x4 grid)
- ✓ Each bar updates independently
- ✓ Bars fill bottom-to-top
- ✓ Color changes to orange above 75%
- ✓ No console errors

---

## 10. Summary Checklist

Before starting any task:
- [ ] State hardware target (RTX 3060 / Ryzen 5700X)
- [ ] Identify target module for changes
- [ ] Propose simplest solution first
- [ ] Confirm Figma specifications

During implementation:
- [ ] Make surgical edits only
- [ ] Use exact Figma dimensions and colors
- [ ] No root clutter (use existing modules)
- [ ] No speculative improvements

After implementation:
- [ ] Define verification test
- [ ] Request user confirmation
- [ ] Loop until success confirmed
- [ ] Clean up __pycache__ automatically

---

**These guardrails are now the law for all Vitreos V3 development.**
