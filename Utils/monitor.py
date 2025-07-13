import time
from typing import Dict

_service_health_status: Dict[str, Dict[str, str]] = {}
server_start_time = time.strftime("%Y-%m-%d %H:%M:%S")

# Global last hit across all services
_global_last_hit = {
    "last_api_hit_time": None,
    "last_api_endpoint": None
}

def update_service_health(service: str, endpoint: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    _service_health_status[service] = {
        "last_hit_time": timestamp,
        "last_endpoint": endpoint
    }

    _global_last_hit["last_api_hit_time"] = timestamp
    _global_last_hit["last_api_endpoint"] = f"{service} -> {endpoint}"

def get_service_health(service: str):
    return _service_health_status.get(service, {
        "last_hit_time": None,
        "last_endpoint": None
    })

def get_all_services_health():
    return {
        "services": _service_health_status,
        "server_start_time": server_start_time,
        "last_api_hit_time": _global_last_hit["last_api_hit_time"],
        "last_api_endpoint": _global_last_hit["last_api_endpoint"]
    }
