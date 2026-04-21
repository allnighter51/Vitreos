"""
Vitreos Telemetry Bridge - V3 to Legacy Tab Adapter
Translates V3 telemetry data format to legacy tab expectations
"""

from typing import Dict, Any


def translate_to_legacy_format(v3_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate V3 telemetry format to legacy tab format.
    
    V3 Format:
        {'cpu': {...}, 'gpu': {...}, 'memory': {...}, 'network': {...}, ...}
    
    Legacy Format:
        Flat dictionary with specific key names expected by tabs
    
    Args:
        v3_data: Telemetry data from TelemetryWorker
    
    Returns:
        Flat dictionary with legacy key names
    """
    cpu = v3_data.get('cpu', {})
    gpu_data = v3_data.get('gpu', [])
    # Handle list from newer telemetry or dict from legacy
    gpu = gpu_data[0] if isinstance(gpu_data, list) and gpu_data else (gpu_data if isinstance(gpu_data, dict) else {})

    memory = v3_data.get('memory', {})
    network = v3_data.get('network', {})
    storage = v3_data.get('storage', {})
    thermal = v3_data.get('thermal', {})
    
    # Build legacy format dictionary
    legacy_data = {
        # CPU keys
        'cpu_name': cpu.get('name', 'Unknown CPU'),
        'cpu_percent': cpu.get('totalLoad', 0),
        'cpu_freq': cpu.get('clock', 0),
        'cpu_temp': cpu.get('temp', 0),
        'cpu_cores': cpu.get('cores', []),
        'cpu_count': cpu.get('coreCount', 0),
        
        # GPU keys
        'gpu_name': gpu.get('name', 'Unknown GPU'),
        'gpu_usage': gpu.get('usage', 0),
        'gpu_temp': gpu.get('temp', 0),
        'gpu_vram_used': gpu.get('vramUsed', 0),
        'gpu_vram_total': gpu.get('vramTotal', 0),
        'gpu_vram_percent': gpu.get('vramPercent', 0),
        'gpu_core_clock': gpu.get('coreClock', 0),
        'gpu_mem_clock': gpu.get('memClock', 0),
        'gpu_power': gpu.get('power', 0),
        'gpu_fan_speed': gpu.get('fanSpeed', 0),
        'gpu_status': gpu.get('status', 'normal'),
        
        # Memory keys
        'memory_used': memory.get('totalUsed', 0) * (1024**3),  # Convert GB to bytes
        'memory_total': memory.get('totalCapacity', 0) * (1024**3),
        'memory_percent': (memory.get('totalUsed', 0) / memory.get('totalCapacity', 1) * 100) if memory.get('totalCapacity', 0) > 0 else 0,
        'memory_available': (memory.get('totalCapacity', 0) - memory.get('totalUsed', 0)) * (1024**3),
        
        # Network keys
        'net_sent_mbps': network.get('uploadMbps', 0),
        'net_recv_mbps': network.get('downloadMbps', 0),
        'net_sent_bytes': network.get('uploadMbps', 0) * (1024**2),  # Approximate
        'net_recv_bytes': network.get('downloadMbps', 0) * (1024**2),
        'ping': network.get('latencyMs', 0),
        'jitter': network.get('jitter', 0),
        'gateway_latency': network.get('gatewayLatency', 0),
        'dns_latency': network.get('dnsLatency', 0),
        'download_mbps': network.get('downloadMbps', 0),
        'upload_mbps': network.get('uploadMbps', 0),
        'packet_loss': network.get('packetLoss', 0),
        'primary_nic': network.get('primaryNic', 'ETH'),
        'interfaces': network.get('interfaces', []),
        'net_hogs': v3_data.get('networkHogs', []),
        
        # Storage keys
        'disk_percent': 0,  # Will be calculated from drives
        'disk_free': 0,
        'disk_total': 0,
        'disk_used': 0,
        
        # Thermal keys
        'temps': thermal.get('temps', []),
        'fans': thermal.get('fans', []),
        'ambient_temp': thermal.get('ambientTemp', 0),
    }
    
    # Calculate disk stats from drives
    drives = storage.get('drives', [])
    if drives:
        total_used = sum(d.get('used', 0) for d in drives)
        total_capacity = sum(d.get('total', 0) for d in drives)
        
        legacy_data['disk_used'] = total_used * (1024**2)  # MB to bytes
        legacy_data['disk_total'] = total_capacity * (1024**2)
        legacy_data['disk_free'] = legacy_data['disk_total'] - legacy_data['disk_used']
        legacy_data['disk_percent'] = (total_used / total_capacity * 100) if total_capacity > 0 else 0
    
    return legacy_data


__all__ = ['translate_to_legacy_format']


