"""
Alerts module for the Mini Cloud Platform Simulator.
Refactored to only expose ArmorIQ-governed endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, Literal

from system.state import state
from system.logger import log_action
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp/alerts", tags=["alerts"])

# ----- Request Models -----
class CreateAlertRequest(BaseModel):
    # agent_id removed/ignored for sim
    type: Literal["cpu", "memory", "disk", "network", "security", "service", "custom"]
    msg: str
    severity: Literal["low", "medium", "high", "critical"]
    resource_id: Optional[str] = None
    class Config:
        extra = "ignore"

class ResolveAlertRequest(BaseModel):
    alert_id: str
    resolution_note: Optional[str] = None
    class Config:
        extra = "ignore"

# ----- Endpoints -----
@router.post("/create")
def create_alert(req: CreateAlertRequest, x_user_email: str = Header("simulation", alias="X-ArmorIQ-User-Email")):
    """
    Create a new alert (Simulation/Environment Endpoint).
    NOT ArmorIQ-governed as this represents external system faults.
    """
    # No verify_armoriq dependency needed for fault injection
    
    alert = state.add_alert({
        "type": req.type,
        "msg": req.msg,
        "severity": req.severity,
        "status": "open",
        "resource_id": req.resource_id,
        "created_by": "simulator", # Fixed for sim
    })
    
    logger.info(f"Simulated Alert Created: {alert['id']} ({req.type})")
    
    return {
        "status": "success",
        "message": f"Alert created with ID '{alert['id']}'",
        "alert": alert,
    }

# ----- Dependency -----
def verify_armoriq(x_armoriq_intent: str = Header(None, alias="X-ArmorIQ-Intent-ID")):
    """Verifies the request is authorized via ArmorIQ."""
    if not x_armoriq_intent:
        logger.warning(f"Rejecting unauthorized request: Missing X-ArmorIQ-Intent-ID")
        raise HTTPException(status_code=401, detail="Unauthorized: ArmorIQ Intent Required")
    return x_armoriq_intent

# ----- Endpoints -----
@router.post("/resolve")
def resolve_alert(req: ResolveAlertRequest, intent_id: str = Depends(verify_armoriq), x_user_email: str = Header("unknown", alias="X-ArmorIQ-User-Email")):
    """Resolve an alert (ArmorIQ Governed)."""
    logger.info(f"Authorized Request [Intent: {intent_id}] from {x_user_email}")
    
    # Find the alert
    alert = None
    for a in state.get_alerts():
        if a["id"] == req.alert_id:
            alert = a
            break
    
    if not alert:
        logger.error(f"Alert {req.alert_id} not found")
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.get("resolved"):
        logger.error(f"Alert {req.alert_id} already resolved")
        raise HTTPException(status_code=400, detail="Alert already resolved")
    
    # Simulate resolution
    resolved = state.resolve_alert(req.alert_id)
    if resolved:
        resolved["status"] = "resolved"
        resolved["resolved_by"] = x_user_email
        if req.resolution_note:
            resolved["resolution_note"] = req.resolution_note
            
    # Log Action
    logger.info(f"Alert {req.alert_id} resolved")
    log_action("alert.resolved", user=x_user_email, alert_id=req.alert_id, intent=intent_id)
    
    return {
        "status": "success",
        "message": f"Alert '{req.alert_id}' resolved",
        "alert": resolved,
    }

# ----- Utility Endpoints (Read-Only) -----

@router.get("/")
def list_alerts(status: Optional[str] = None, severity: Optional[str] = None):
    """List all alerts with filters."""
    alerts = state.get_alerts()
    
    if status == "open":
        alerts = [a for a in alerts if not a.get("resolved")]
    elif status == "resolved":
        alerts = [a for a in alerts if a.get("resolved")]
        
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
        
    return {"total": len(alerts), "alerts": alerts}

@router.get("/{alert_id}")
def get_alert(alert_id: str):
    """Get a specific alert."""
    for alert in state.get_alerts():
        if alert["id"] == alert_id:
            return alert
    raise HTTPException(status_code=404, detail="Alert not found")
