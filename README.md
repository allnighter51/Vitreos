# Vitreos

Lightweight Windows monitoring service with optional Discord heartbeat updates.

## Canonical Runtime

Vitreos now has one supported runtime path:

- `scripts/install_requirements_terminal.bat`
- `scripts/launch_vitreos_terminal.bat`
- or directly: `python src/main.py`

Legacy files (`vitreos_main.py` and `@workspace/src/main.py`) are compatibility wrappers that forward to `src/main.py`.

## What It Monitors

- CPU usage via `psutil`
- GPU VRAM, temperature, and fan where the `pynvml` module is available
- Basic security status marker for failed-login events
- Discord webhook heartbeat updates (when configured)

## Configuration

Primary config files:

- `config/settings.json`
  - Supported webhook keys:
    - flat: `webhook_url`
    - nested: `discord.webhook_url`
- `config/webhooks.json`
  - optional webhook-focused config (`discord_webhook_url`, `fallback_console`)

If webhook is missing or invalid, Vitreos keeps running and logs to console.

## Installation

Install dependencies:

```bat
scripts\install_requirements_terminal.bat
```

This installs:

- `psutil`
- `nvidia-ml-py` (provides the `pynvml` module)
- `pywin32`
- `requests`
- optional `PyQt6` (legacy GUI compatibility only)

## Notes

- `vitreos.spec` is aligned to package `src/main.py`.
- The legacy GUI implementation is not the recommended runtime.
