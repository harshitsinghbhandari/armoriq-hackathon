"""
Data module for the Mini Cloud Platform Simulator.
Handles database management operations.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from auth.server import get_current_user
from pydantic import BaseModel
from typing import Optional

from system.state import state
from system.logger import log_action
from policy.engine import allow

router = APIRouter(prefix="/mcp/data", tags=["data"])


# ----- Request Models -----
class BackupRequest(BaseModel):
    agent_id: str
    db_id: str
    backup_name: Optional[str] = None


class RestoreRequest(BaseModel):
    agent_id: str
    db_id: str
    backup_name: str


class PurgeRequest(BaseModel):
    agent_id: str
    db_id: str
    confirm: bool = False


# ----- Endpoints -----
@router.post("/backup")
def backup_database(req: BackupRequest, current_user: dict = Depends(get_current_user)):
    """Create a backup of a database."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "data.backup", {
        "db_id": req.db_id,
        "agent_id": req.agent_id
    })
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")
    
    db = state.get_database(req.db_id)
    if not db:
        raise HTTPException(status_code=404, detail="Database not found")
    
    now = datetime.now()
    backup_name = req.backup_name or f"backup_{now.strftime('%Y%m%d_%H%M%S')}"
    
    # Update database with backup info
    state.update_database(req.db_id, {
        "last_backup": now.isoformat(),
        "last_backup_name": backup_name,
        "backup_count": db.get("backup_count", 0) + 1,
    })
    
    from policy.engine import consume_quota
    consume_quota(current_user, "data.backup", {
        "db_id": req.db_id,
        "agent_id": req.agent_id
    })
    
    log_action("data.backup", user=current_user["username"], db_id=req.db_id, backup_name=backup_name)
    
    return {
        "status": "success",
        "message": f"Database '{req.db_id}' backed up as '{backup_name}'",
        "backup_name": backup_name,
        "timestamp": now.isoformat(),
        "database": state.get_database(req.db_id),
    }


@router.post("/restore")
def restore_database(req: RestoreRequest, current_user: dict = Depends(get_current_user)):
    """Restore a database from a backup."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "data.restore", {
        "db_id": req.db_id, 
        "backup_name": req.backup_name,
        "agent_id": req.agent_id
    })
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")
    
    db = state.get_database(req.db_id)
    if not db:
        raise HTTPException(status_code=404, detail="Database not found")
    
    now = datetime.now()
    
    # Simulate restore
    state.update_database(req.db_id, {
        "status": "healthy",
        "last_restore": now.isoformat(),
        "restored_from": req.backup_name,
    })
    
    from policy.engine import consume_quota
    consume_quota(current_user, "data.restore", {
        "db_id": req.db_id, 
        "backup_name": req.backup_name,
        "agent_id": req.agent_id
    })
    
    log_action("data.restore", user=current_user["username"], db_id=req.db_id, backup_name=req.backup_name)
    
    return {
        "status": "success",
        "message": f"Database '{req.db_id}' restored from '{req.backup_name}'",
        "timestamp": now.isoformat(),
        "database": state.get_database(req.db_id),
    }


@router.post("/purge")
def purge_database(req: PurgeRequest, current_user: dict = Depends(get_current_user)):
    """Purge all data from a database (requires confirmation)."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "data.purge", {
        "db_id": req.db_id,
        "agent_id": req.agent_id
    })
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")
    
    db = state.get_database(req.db_id)
    if not db:
        raise HTTPException(status_code=404, detail="Database not found")
    
    if not req.confirm:
        raise HTTPException(
            status_code=400, 
            detail="Purge requires confirmation. Set 'confirm': true"
        )
    
    now = datetime.now()
    old_size = db.get("size_mb", 0)
    
    # Simulate purge
    state.update_database(req.db_id, {
        "size_mb": 0,
        "last_purge": now.isoformat(),
        "status": "empty",
    })
    
    from policy.engine import consume_quota
    consume_quota(current_user, "data.purge", {
        "db_id": req.db_id,
        "agent_id": req.agent_id
    })
    
    log_action("data.purge", user=current_user["username"], db_id=req.db_id, purged_size_mb=old_size)
    
    return {
        "status": "success",
        "message": f"Database '{req.db_id}' purged ({old_size} MB cleared)",
        "purged_size_mb": old_size,
        "timestamp": now.isoformat(),
        "database": state.get_database(req.db_id),
    }


# ----- Utility Endpoints -----
@router.get("/list")
def list_databases():
    """List all databases."""
    return {"databases": list(state.get_databases().values())}


@router.get("/{db_id}")
def get_database(db_id: str):
    """Get a specific database."""
    db = state.get_database(db_id)
    if not db:
        raise HTTPException(status_code=404, detail="Database not found")
    return db
