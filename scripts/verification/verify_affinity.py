#!/usr/bin/env python3
"""
Verification Script 1: Affinity Lock Validator
Tests if process affinity is correctly set to physical cores only
"""

import psutil
import sys

def verify_affinity(pid: int) -> bool:
    """
    Verify that a process is locked to physical cores (0,2,4,6,8,10,12,14).
    
    Args:
        pid: Process ID to check
    
    Returns:
        True if affinity is correctly set, False otherwise
    """
    try:
        proc = psutil.Process(pid)
        affinity = proc.cpu_affinity()
        
        # Expected physical cores for Ryzen 5700X (8C/16T)
        expected_physical = [0, 2, 4, 6, 8, 10, 12, 14]
        
        print(f"[VERIFY] Process: {proc.name()} (PID {pid})")
        print(f"[VERIFY] Current Affinity: {affinity}")
        print(f"[VERIFY] Expected Physical: {expected_physical}")
        
        # Check if affinity matches physical cores
        if set(affinity) == set(expected_physical):
            print("[VERIFY] ✓ PASS - Affinity correctly locked to physical cores")
            return True
        else:
            print("[VERIFY] ✗ FAIL - Affinity does not match physical cores")
            return False
    
    except psutil.NoSuchProcess:
        print(f"[VERIFY] ✗ ERROR - Process {pid} does not exist")
        return False
    except psutil.AccessDenied:
        print(f"[VERIFY] ✗ ERROR - Access denied for process {pid}")
        return False
    except Exception as e:
        print(f"[VERIFY] ✗ ERROR - {e}")
        return False


def main():
    """Run affinity verification."""
    if len(sys.argv) < 2:
        print("Usage: python verify_affinity.py <PID>")
        print("Example: python verify_affinity.py 1234")
        sys.exit(1)
    
    try:
        pid = int(sys.argv[1])
        result = verify_affinity(pid)
        sys.exit(0 if result else 1)
    except ValueError:
        print("[VERIFY] ✗ ERROR - Invalid PID (must be integer)")
        sys.exit(1)


if __name__ == "__main__":
    main()
