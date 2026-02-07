"""
Alerts module for the Mini Cloud Platform Simulator.
Handles system alerts and notifications.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional

from system.state import state
from system.logger import log_action
from policy.engine import allow
from fastapi import Depends
from auth.server import get_current_user

router = APIRouter(prefix="/mcp/alerts", tags=["alerts"])


# ----- Request Models -----
class CreateAlertRequest(BaseModel):
    agent_id: str
    type: Literal["cpu", "memory", "disk", "network", "security", "service", "custom"]
    msg: str
    severity: Literal["low", "medium", "high", "critical"]
    resource_id: Optional[str] = None


class ResolveAlertRequest(BaseModel):
    agent_id: str
    alert_id: str
    resolution_note: Optional[str] = None


# ----- Endpoints -----
@router.post("/create")
def create_alert(req: CreateAlertRequest, current_user: dict = Depends(get_current_user)):
    """Create a new alert."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "alert.create", {
        "type": req.type,
        "severity": req.severity,
        "agent_id": req.agent_id
    })
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")

    alert = state.add_alert({
        "type": req.type,
        "msg": req.msg,
        "severity": req.severity,
        "status": "open",
        "resource_id": req.resource_id,
        "created_by": current_user["username"],
    })
    
    from policy.engine import consume_quota
    consume_quota(current_user, "alert.create", {
        "type": req.type,
        "severity": req.severity,
        "agent_id": req.agent_id
    })
    
    log_action("alert.created", user=current_user["username"], alert_id=alert["id"], 
               severity=req.severity, type=req.type)
    
    return {
        "status": "success",
        "message": f"Alert created with ID '{alert['id']}'",
        "alert": alert,
    }


@router.post("/resolve")
def resolve_alert(req: ResolveAlertRequest, current_user: dict = Depends(get_current_user)):
    """Resolve an existing alert."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "alert.resolve", {
        "alert_id": req.alert_id,
        "agent_id": req.agent_id
    })
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")

    # Find the alert
    alert = None
    for a in state.get_alerts():
        if a["id"] == req.alert_id:
            alert = a
            break
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert.get("resolved"):
        raise HTTPException(status_code=400, detail="Alert already resolved")
    
    # Resolve it
    resolved = state.resolve_alert(req.alert_id)
    if resolved:
        resolved["status"] = "resolved"
        resolved["resolved_by"] = current_user["username"]
        if req.resolution_note:
            resolved["resolution_note"] = req.resolution_note
    
    from policy.engine import consume_quota
    consume_quota(current_user, "alert.resolve", {
        "alert_id": req.alert_id,
        "agent_id": req.agent_id
    })
    
    log_action("alert.resolved", user=current_user["username"], alert_id=req.alert_id)
    
    return {
        "status": "success",
        "message": f"Alert '{req.alert_id}' resolved",
        "alert": resolved,
    }


@router.get("/")
def list_alerts(
    status: Optional[Literal["open", "resolved"]] = None,
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None,
):
    """List all alerts with optional filtering."""
    alerts = state.get_alerts()
    
    # Filter by status
    if status == "open":
        alerts = [a for a in alerts if not a.get("resolved")]
    elif status == "resolved":
        alerts = [a for a in alerts if a.get("resolved")]
    
    # Filter by severity
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
    
    return {
        "total": len(alerts),
        "alerts": alerts,
    }


@router.get("/{alert_id}")
def get_alert(alert_id: str):
    """Get a specific alert."""
    for alert in state.get_alerts():
        if alert["id"] == alert_id:
            return alert
    raise HTTPException(status_code=404, detail="Alert not found")
