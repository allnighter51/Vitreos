"""
Vitreos Lazy Loader - On-Demand Module Initialization
Defers heavy module loading until user actually needs them
"""

from typing import Dict, Any, Optional, Callable
from src.core.vitreos_logger import v_debug, v_info

class LazyLoader:
    """
    Lazy-loading manager for heavy modules.
    
    Modules are only imported and initialized when first accessed.
    Subsequent accesses return the cached instance.
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._loaders: Dict[str, Callable] = {}
    
    def register(self, name: str, loader: Callable) -> None:
        """
        Register a lazy-loadable module.
        
        Args:
            name: Module identifier (e.g., 'console', 'cmd_engine')
            loader: Function that imports and initializes the module
        """
        self._loaders[name] = loader
        v_debug(f"Registered lazy loader: {name}")
    
    def get(self, name: str) -> Optional[Any]:
        """
        Get a module instance (loads on first access).
        
        Args:
            name: Module identifier
        
        Returns:
            Module instance or None if not registered
        """
        # Return cached instance if available
        if name in self._cache:
            v_debug(f"Returning cached module: {name}")
            return self._cache[name]
        
        # Load module if loader is registered
        if name in self._loaders:
            v_info(f"Lazy-loading module: {name}")
            try:
                instance = self._loaders[name]()
                self._cache[name] = instance
                v_info(f"Module loaded successfully: {name}")
                return instance
            except Exception as e:
                v_info(f"Failed to load module {name}: {e}")
                return None
        
        v_debug(f"No loader registered for: {name}")
        return None
    
    def is_loaded(self, name: str) -> bool:
        """Check if a module is already loaded"""
        return name in self._cache
    
    def unload(self, name: str) -> None:
        """Unload a module from cache"""
        if name in self._cache:
            del self._cache[name]
            v_debug(f"Unloaded module: {name}")


# Global lazy loader instance
_lazy_loader = LazyLoader()


def register_lazy_module(name: str, loader: Callable) -> None:
    """Register a module for lazy loading"""
    _lazy_loader.register(name, loader)


def get_lazy_module(name: str) -> Optional[Any]:
    """Get a lazy-loaded module (loads on first access)"""
    return _lazy_loader.get(name)


def is_module_loaded(name: str) -> bool:
    """Check if a module is loaded"""
    return _lazy_loader.is_loaded(name)


__all__ = ['LazyLoader', 'register_lazy_module', 'get_lazy_module', 'is_module_loaded']
