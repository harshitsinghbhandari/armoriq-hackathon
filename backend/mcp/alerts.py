"""
Alerts module for the Mini Cloud Platform Simulator.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Literal
from system.state import state
from system.logger import log_action
import logging
from mcp.registry import registry, ToolParameter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp/alerts", tags=["alerts"])

# --- Tools ---

@registry.register(
    name="alert.resolve",
    description="Resolve an alert by ID",
    parameters=[
        ToolParameter(name="alert_id", type="string", description="ID of the alert to resolve"),
        ToolParameter(name="resolution_note", type="string", description="Note explaining the resolution"),
        ToolParameter(name="user_email", type="string", description="Email of the user performing the action", required=False)
    ]
)
def resolve_alert(alert_id: str, resolution_note: str, user_email: str = "unknown", **kwargs):
    """Resolve an alert (ArmorIQ Governed Tool)."""
    logger.info(f"Executing alert.resolve for {alert_id}")
    
    alert = state.get_alert(alert_id)
    if not alert:
        raise ValueError(f"Alert {alert_id} not found")
        
    if alert.get("resolved"):
        raise ValueError(f"Alert {alert_id} already resolved")

    # Resolve
    resolved = state.resolve_alert(alert_id)
    if resolved:
        resolved["status"] = "resolved"
        resolved["resolved_by"] = user_email
        resolved["resolution_note"] = resolution_note
    
    # Log
    log_action("alert.resolved", user=user_email, alert_id=alert_id, note=resolution_note)
    
    return {
        "status": "success", 
        "message": f"Alert {alert_id} resolved",
        "alert": resolved
    }

# --- Simulation / Fault Injection (Not Governed) ---

class CreateAlertRequest(BaseModel):
    type: Literal["cpu", "memory", "disk", "network", "security", "service", "custom"]
    msg: str
    severity: Literal["low", "medium", "high", "critical"]
    resource_id: Optional[str] = None
    agent_id: Optional[str] = None # Support legacy field
    class Config:
        extra = "ignore"

@router.post("/create")
def create_alert(req: CreateAlertRequest):
    """
    Create a new alert (Simulation/Environment Endpoint).
    NOT ArmorIQ-governed as this represents external system faults.
    """
    alert = state.add_alert({
        "type": req.type,
        "msg": req.msg,
        "severity": req.severity,
        "status": "open",
        "resource_id": req.resource_id,
        "created_by": "simulator",
    })
    
    logger.info(f"Simulated Alert Created: {alert['id']} ({req.type})")
    
    return {
        "status": "success",
        "message": f"Alert created with ID '{alert['id']}'",
        "alert": alert,
    }

# --- Read-Only Endpoints ---

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
