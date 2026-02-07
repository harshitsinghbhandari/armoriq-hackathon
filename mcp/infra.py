"""
Infrastructure module for the Mini Cloud Platform Simulator.
Handles service management operations.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional

from system.state import state
from system.logger import log_action
from policy.engine import allow

from fastapi import Depends
from auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp/infra", tags=["infrastructure"])


# ----- Request Models -----
class RestartRequest(BaseModel):
    agent_id: str
    service_id: str


class ScaleRequest(BaseModel):
    agent_id: str
    service_id: str
    replicas: int


class ShutdownRequest(BaseModel):
    agent_id: str
    service_id: str


class DeployRequest(BaseModel):
    agent_id: str
    service_id: str
    name: str
    port: int
    version: Optional[str] = "1.0.0"


# ----- Endpoints -----
@router.post("/restart")
def restart_service(req: RestartRequest, current_user: dict = Depends(get_current_user)):
    """Restart a service."""
    logger.info(f"Authenticated user: {current_user['username']} Roles: {current_user['roles']}")
    
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        logger.warning(f"Identity mismatch: {req.agent_id} != {current_user['username']}")
        raise HTTPException(status_code=403, detail="Identity mismatch")
    
    # Check Policy
    allowed, reason = allow(current_user, "infra.restart", {
        "service_id": req.service_id,
        "agent_id": req.agent_id
    })
    
    if not allowed:
        logger.warning(f"Access denied for user '{current_user['username']}': {reason}")
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")
    
    service = state.get_service(req.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Simulate restart
    state.update_service(req.service_id, {
        "status": "running",
        "health": "healthy",
        "restarted_at": datetime.now().isoformat(),
    })
    
    # Consume Quota (Rate Limiting)
    from policy.engine import consume_quota
    consume_quota(current_user, "infra.restart", {
        "service_id": req.service_id,
        "agent_id": req.agent_id
    })
    
    logger.info(f"Service restarted by {current_user['username']}")
    log_action("infra.restarted", user=current_user["username"], service_id=req.service_id)
    
    return {
        "status": "success",
        "message": f"Service '{req.service_id}' restarted",
        "service": state.get_service(req.service_id),
    }


@router.post("/scale")
def scale_service(req: ScaleRequest, current_user: dict = Depends(get_current_user)):
    """Scale a service to specified replicas."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "infra.scale", {
        "service_id": req.service_id, 
        "replicas": req.replicas,
        "agent_id": req.agent_id
    })
    
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")
    
    service = state.get_service(req.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    old_replicas = service.get("replicas", 1)
    state.update_service(req.service_id, {
        "replicas": req.replicas,
        "scaled_at": datetime.now().isoformat(),
    })
    
    log_action("infra.scaled", user=current_user["username"], service_id=req.service_id,
               old_replicas=old_replicas, new_replicas=req.replicas)
    
    return {
        "status": "success",
        "message": f"Service '{req.service_id}' scaled from {old_replicas} to {req.replicas} replicas",
        "service": state.get_service(req.service_id),
    }


@router.post("/shutdown")
def shutdown_service(req: ShutdownRequest, current_user: dict = Depends(get_current_user)):
    """Shutdown a service."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "infra.shutdown", {
        "service_id": req.service_id,
        "agent_id": req.agent_id
    })
    
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")
    
    service = state.get_service(req.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    state.update_service(req.service_id, {
        "status": "stopped",
        "health": "offline",
        "stopped_at": datetime.now().isoformat(),
    })
    
    log_action("infra.shutdown", user=current_user["username"], service_id=req.service_id)
    
    return {
        "status": "success",
        "message": f"Service '{req.service_id}' has been shut down",
        "service": state.get_service(req.service_id),
    }


@router.post("/deploy")
def deploy_service(req: DeployRequest, current_user: dict = Depends(get_current_user)):
    """Deploy a new service."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "infra.deploy", {
        "service_id": req.service_id, 
        "name": req.name, 
        "port": req.port,
        "agent_id": req.agent_id
    })
    
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")
    
    if state.get_service(req.service_id):
        raise HTTPException(status_code=400, detail="Service already exists")
    
    state.add_service(req.service_id, {
        "name": req.name,
        "status": "running",
        "port": req.port,
        "health": "healthy",
        "version": req.version,
        "replicas": 1,
    })
    
    log_action("infra.deployed", user=current_user["username"], service_id=req.service_id,
               name=req.name, port=req.port)
    
    return {
        "status": "success",
        "message": f"Service '{req.service_id}' deployed successfully",
        "service": state.get_service(req.service_id),
    }


# ----- Utility Endpoints -----
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
