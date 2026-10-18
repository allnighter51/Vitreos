"""
Vitreos Security Tab - Thin Alias Module
Enforces Single Source of Truth architecture by exporting the unified SOCTab from tab_soc.
"""

from src.tabs.tab_soc import SOCTab, SOCTab as SecurityTab

__all__ = ['SOCTab', 'SecurityTab']
