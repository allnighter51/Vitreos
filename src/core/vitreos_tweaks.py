"""
Vitreos Tweaks Engine
OS-level optimization and system repair utilities
"""

import subprocess
import winreg
from typing import Tuple


class SystemTweaker:
    """OS-level optimization engine for Windows performance tweaks"""
    
    @staticmethod
    def enable_ultimate_performance() -> Tuple[bool, str]:
        """
        Unlock and activate Windows Ultimate Performance power plan
        Returns: (success: bool, message: str)
        """
        try:
            # Step 1: Duplicate the Ultimate Performance scheme
            result = subprocess.run(
                ["powercfg", "-duplicatescheme", "e9a42b02-d5df-448d-aa00-03f14749eb61"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                return False, f"Failed to duplicate scheme: {result.stderr}"
            
            # Extract GUID from output (format: "Power Scheme GUID: {GUID}")
            output = result.stdout
            if "Power Scheme GUID:" in output:
                guid = output.split("Power Scheme GUID:")[1].strip().split()[0]
                
                # Step 2: Activate the scheme
                activate_result = subprocess.run(
                    ["powercfg", "-setactive", guid],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if activate_result.returncode == 0:
                    return True, f"Ultimate Performance mode activated (GUID: {guid})"
                else:
                    return False, f"Failed to activate scheme: {activate_result.stderr}"
            else:
                return False, "Could not parse GUID from powercfg output"
                
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    @staticmethod
    def disable_game_dvr() -> Tuple[bool, str]:
        """
        Disable Xbox Game DVR and Game Bar
        Returns: (success: bool, message: str)
        """
        try:
            # Registry edit 1: HKCU\System\GameConfigStore
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"System\GameConfigStore")
                winreg.SetValueEx(key, "GameDVR_Enabled", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
            except Exception as e:
                return False, f"Failed to edit HKCU registry: {str(e)}"
            
            # Registry edit 2: HKLM\SOFTWARE\Policies\Microsoft\Windows\GameDVR
            try:
                key = winreg.CreateKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Policies\Microsoft\Windows\GameDVR"
                )
                winreg.SetValueEx(key, "AllowGameDVR", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
            except Exception as e:
                return False, f"Failed to edit HKLM registry: {str(e)}"
            
            return True, "Game DVR and Xbox Game Bar disabled successfully"
            
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    @staticmethod
    def disable_telemetry() -> Tuple[bool, str]:
        """
        Disable Windows telemetry and DiagTrack service
        Returns: (success: bool, message: str)
        """
        try:
            messages: list[str] = []
            
            # Stop DiagTrack service
            stop_result = subprocess.run(
                ["sc", "stop", "DiagTrack"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            messages.append(f"Stop DiagTrack: {stop_result.stdout.strip()}")
            
            # Disable DiagTrack service
            disable_result = subprocess.run(
                ["sc", "config", "DiagTrack", "start=", "disabled"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            messages.append(f"Disable DiagTrack: {disable_result.stdout.strip()}")
            
            # Registry edit: Disable telemetry data collection
            try:
                key = winreg.CreateKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Policies\Microsoft\Windows\DataCollection"
                )
                winreg.SetValueEx(key, "AllowTelemetry", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                messages.append("Registry: AllowTelemetry set to 0")
            except Exception as e:
                messages.append(f"Registry edit failed: {str(e)}")
            
            return True, " | ".join(messages)
            
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    @staticmethod
    def flush_dns_and_cache() -> Tuple[bool, str]:
        """
        Flush DNS cache and clear Windows temp directories
        Returns: (success: bool, message: str)
        """
        try:
            messages: list[str] = []
            
            # Flush DNS
            dns_result = subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if dns_result.returncode == 0:
                messages.append("DNS cache flushed")
            else:
                messages.append(f"DNS flush failed: {dns_result.stderr}")
            
            # Clear %TEMP%
            import os
            temp_path = os.environ.get("TEMP", "")
            if temp_path:
                subprocess.run(
                    ["cmd", "/c", f"del /q /f /s {temp_path}\\*"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                messages.append(f"User TEMP cleared")
            
            # Clear C:\Windows\Temp
            subprocess.run(
                ["cmd", "/c", r"del /q /f /s C:\Windows\Temp\*"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            messages.append("Windows TEMP cleared")
            
            return True, " | ".join(messages)
            
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    @staticmethod
    def run_system_repair() -> Tuple[bool, str]:
        """
        Run SFC and DISM system repair (BLOCKING - use in thread)
        Returns: (success: bool, message: str)
        """
        try:
            messages: list[str] = []
            
            # Run SFC scan
            messages.append("Running SFC /scannow (this may take several minutes)...")
            sfc_result = subprocess.run(
                ["sfc", "/scannow"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if sfc_result.returncode == 0:
                messages.append("SFC scan completed successfully")
            else:
                messages.append(f"SFC scan completed with warnings: {sfc_result.returncode}")
            
            # Run DISM repair
            messages.append("Running DISM /RestoreHealth (this may take several minutes)...")
            dism_result = subprocess.run(
                ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if dism_result.returncode == 0:
                messages.append("DISM repair completed successfully")
            else:
                messages.append(f"DISM repair completed with warnings: {dism_result.returncode}")
            
            return True, "\n".join(messages)
            
        except Exception as e:
            return False, f"Exception: {str(e)}"


