"""
Vitreos Executable Build Runner
Invokes PyInstaller using Vitreos.spec and validates the generated executable.
"""

import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).parent.resolve()
    spec_file = project_root / "Vitreos.spec"
    dist_dir = project_root / "dist"
    exe_path = dist_dir / "Vitreos.exe"

    print("=================================================================")
    print(" VITREOS // NATIVE STANDALONE WINDOWS EXECUTABLE PIPELINE")
    print("=================================================================")
    print(f"Project Root: {project_root}")
    print(f"Spec File:    {spec_file}")
    print()

    if not spec_file.exists():
        print(f"Error: Spec file not found at {spec_file}")
        sys.exit(1)

    # Execute PyInstaller
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(spec_file)]
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(project_root))

    if result.returncode != 0:
        print(f"PyInstaller build failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    if not exe_path.exists():
        print(f"Error: Expected executable not found at {exe_path}")
        sys.exit(1)

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print()
    print("=================================================================")
    print(" BUILD SUCCESSFUL")
    print(f" Executable: {exe_path}")
    print(f" File Size:  {size_mb:.2f} MB")
    print("=================================================================")


if __name__ == "__main__":
    main()
