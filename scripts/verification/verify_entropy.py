#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification Script 2: Entropy Scanner Validator
Tests Shannon entropy calculation against known process names
"""

import math
import sys

def calculate_entropy(text: str) -> float:
    """
    Calculate Shannon entropy H(X) = -Σ P(xi) * log2(P(xi))
    
    Args:
        text: Input string to analyze
    
    Returns:
        Entropy value (0.0 to ~log2(len(charset)))
    """
    if not text:
        return 0.0
    
    # Count character frequencies
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    
    # Calculate probabilities and entropy
    length = len(text)
    entropy = 0.0
    
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy


def verify_entropy_scanner():
    """Test entropy scanner against known process names."""
    
    test_cases = [
        # Normal process names (low entropy)
        ("chrome.exe", False, "Normal browser process"),
        ("explorer.exe", False, "Windows Explorer"),
        ("notepad.exe", False, "Text editor"),
        ("python.exe", False, "Python interpreter"),
        
        # Suspicious randomized names (high entropy)
        ("xK9mQ2pL7nR4sT8vW.exe", True, "Randomized malware name"),
        ("aB3dE5fG7hI9jK1lM.exe", True, "Obfuscated process"),
        ("zXcVbNmAsD1qW2eR3.exe", True, "Random character mix"),
        ("q1w2e3r4t5y6u7i8o9.exe", True, "Alphanumeric random"),
        
        # Edge cases
        ("a.exe", False, "Single character"),
        ("aaaaaaa.exe", False, "Repeated character (low entropy)"),
        ("System", False, "Windows system process"),
    ]
    
    print("[VERIFY] Entropy Scanner Test Suite")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for process_name, should_flag, description in test_cases:
        entropy = calculate_entropy(process_name)
        is_suspicious = entropy > 4.0  # Adjusted threshold
        
        # Check if result matches expectation
        if is_suspicious == should_flag:
            status = "[PASS]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1
        
        flag_indicator = "!" if is_suspicious else " "
        print(f"{status} | {flag_indicator} {process_name:20s} | H={entropy:.2f} | {description}")
    
    print("=" * 60)
    print(f"[VERIFY] Results: {passed} passed, {failed} failed")
    
    return failed == 0


def main():
    """Run entropy scanner verification."""
    result = verify_entropy_scanner()
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
