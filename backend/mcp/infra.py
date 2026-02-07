from fastapi import APIRouter
from .registry import registry, ToolParameter
from system.state import state
import logging
import time

logger = logging.getLogger("mcp.infra")

router = APIRouter(prefix="/mcp/infra", tags=["infra"])

# --- Read-Only / Monitoring Endpoints ---

@router.get("/list")
def list_services_endpoint():
    """List all infrastructure services (API Endpoint)."""
    return {"services": list(state.get_services().values())}

# --- Tools ---

@registry.register(
    name="infra.list",
    description="List all infrastructure services",
    parameters=[]
)
def list_services():
    return {"services": list(state.get_services().values())}

@registry.register(
    name="infra.restart",
    description="Restart a service by ID",
    parameters=[
        ToolParameter(name="service_id", type="string", description="ID of the service to restart"),
        ToolParameter(name="user_email", type="string", description="Email of the user requesting restart")
    ]
)
def restart_service(service_id: str, user_email: str):
    service = state.get_service(service_id)
    if not service:
        raise ValueError(f"Service '{service_id}' not found")

    logger.info(f"Restarting {service_id} requested by {user_email}")
    
    # Simulate restart
    state.update_service(service_id, {"status": "restarting"})
    time.sleep(1) # Simulation
    state.update_service(service_id, {"status": "running", "started_at": time.strftime("%Y-%m-%dT%H:%M:%S")})
    
    state.log_audit({"action": "infra.restart", "target": service_id, "by": user_email})
    return {"status": "restarted", "service": service_id}

@registry.register(
    name="infra.scale",
    description="Scale a service to N replicas",
    parameters=[
        ToolParameter(name="service_id", type="string", description="Service ID"),
        ToolParameter(name="replicas", type="integer", description="Number of replicas")
    ]
)
def scale_service(service_id: str, replicas: int):
    service = state.get_service(service_id)
    if not service:
        raise ValueError(f"Service '{service_id}' not found")
        
    state.update_service(service_id, {"replicas": replicas})
    state.log_audit({"action": "infra.scale", "target": service_id, "replicas": replicas, "by": "agent"})
    return {"status": "scaled", "service": service_id, "replicas": replicas}

@registry.register(
    name="infra.shutdown",
    description="Shutdown/Stop a service",
    parameters=[
        ToolParameter(name="service_id", type="string", description="Service ID")
    ]
)
def shutdown_service(service_id: str):
    service = state.get_service(service_id)
    if not service:
        raise ValueError(f"Service '{service_id}' not found")
        
    state.update_service(service_id, {"status": "stopped"})
    state.log_audit({"action": "infra.shutdown", "target": service_id, "by": "agent"})
    return {"status": "stopped", "service": service_id}
