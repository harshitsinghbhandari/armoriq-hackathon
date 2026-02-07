"""
Infrastructure module for the Mini Cloud Platform Simulator.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from system.state import state
from system.logger import log_action
import logging
from mcp.registry import registry, ToolParameter

logger = logging.getLogger(__name__)

# Read-Only Router
router = APIRouter(prefix="/mcp/infra", tags=["infrastructure"])

# --- Tools ---

@registry.register(
    name="infra.restart",
    description="Restart a service by ID",
    parameters=[
        ToolParameter(name="service_id", type="string", description="ID of the service to restart"),
        ToolParameter(name="user_email", type="string", description="Email of the user performing the action", required=False)
    ]
)
def restart_service(service_id: str, user_email: str = "unknown", **kwargs):
    """Restart a service (ArmorIQ Governed Tool)."""
    logger.info(f"Executing infra.restart for {service_id}")
    
    service = state.get_service(service_id)
    if not service:
        raise ValueError(f"Service {service_id} not found")
    
    # Simulate restart
    state.update_service(service_id, {
        "status": "running",
        "health": "healthy",
        "restarted_at": datetime.now().isoformat(),
    })
    
    # Log Action
    log_action("infra.restarted", user=user_email, service_id=service_id)
    
    return {
        "status": "success",
        "message": f"Service '{service_id}' restarted",
        "service": state.get_service(service_id),
    }

# --- Read-Only Endpoints ---

@router.get("/list")
def list_services():
    """List all services."""
    return {"services": list(state.get_services().values())}

@router.get("/{service_id}")
def get_service(service_id: str):
    """Get a specific service."""
    service = state.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service
