Vitreos V3 Project Guardrails:

    No Root Clutter: Do not create new files in the root directory. Consolidate logic into existing files (vitreos_main_v3.py, vitreos_widgets.py, etc.).

    No Redundancy: Never create .backup, .old, or _v2 files. Edit the "Source of Truth" directly.

    Logic Preservation: Treat C:\Users\Veetl\Desktop\merc\ai workspace\Vitreos\legacy_pyqt as a read-only source for core logic. Do not duplicate its files; refactor their code into the V3 modules.

    Zero One-Offs: Do not create temporary test scripts or fix-it batch files. Run tests within the existing terminal or temporary code blocks that are deleted after use.

    Automatic Cleanup: Always delete __pycache__ and any temporary build artifacts immediately after a task is completed.