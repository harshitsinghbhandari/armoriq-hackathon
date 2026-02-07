from .registry import registry, ToolParameter
from system.state import state
import logging
import time

logger = logging.getLogger("mcp.data")

@registry.register(
    name="data.backup",
    description="Create a backup of a database",
    parameters=[
        ToolParameter(name="db_id", type="string", description="Database ID")
    ]
)
def backup_database(db_id: str):
    db = state.get_database(db_id)
    if not db:
        raise ValueError(f"Database {db_id} not found")
    
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    state.update_database(db_id, {"last_backup": timestamp})
    
    state.log_audit({"action": "data.backup", "target": db_id, "timestamp": timestamp, "by": "agent"})
    return {"status": "success", "db_id": db_id, "timestamp": timestamp}

@registry.register(
    name="data.restore",
    description="Restore a database from backup",
    parameters=[
        ToolParameter(name="db_id", type="string", description="Database ID"),
        ToolParameter(name="backup_id", type="string", description="Backup ID/Timestamp")
    ]
)
def restore_database(db_id: str, backup_id: str):
    db = state.get_database(db_id)
    if not db:
        raise ValueError(f"Database {db_id} not found")
        
    state.update_database(db_id, {"status": "restoring"})
    time.sleep(1)
    state.update_database(db_id, {"status": "healthy"})
    
    state.log_audit({"action": "data.restore", "target": db_id, "backup": backup_id, "by": "agent"})
    return {"status": "restored", "db_id": db_id}

@registry.register(
    name="data.wipe",
    description="Wipe all data from a database (Admin Only)",
    parameters=[
        ToolParameter(name="db_id", type="string", description="Database ID"),
        ToolParameter(name="confirm", type="boolean", description="Confirmation flag")
    ]
)
def wipe_database(db_id: str, confirm: bool):
    if not confirm:
        return {"status": "aborted", "reason": "Confirmation required"}
        
    db = state.get_database(db_id)
    if not db:
        raise ValueError(f"Database {db_id} not found")
        
    # Simulate wipe
    state.update_database(db_id, {"size_mb": 0, "status": "empty"})
    state.log_audit({"action": "data.wipe", "target": db_id, "by": "agent"})
    return {"status": "wiped", "db_id": db_id}
