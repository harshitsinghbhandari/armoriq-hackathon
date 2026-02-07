from .registry import registry, ToolParameter
from system.state import state
import logging
import uuid

logger = logging.getLogger("mcp.security")

@registry.register(
    name="security.rotate_keys",
    description="Rotate API keys for a service or user",
    parameters=[
        ToolParameter(name="target_id", type="string", description="Service or User ID")
    ]
)
def rotate_keys(target_id: str):
    new_key = f"key_{uuid.uuid4().hex[:8]}"
    state.log_audit({"action": "security.rotate_keys", "target": target_id, "by": "agent"})
    return {"status": "rotated", "target_id": target_id, "new_key_hint": new_key[:4] + "***"}

@registry.register(
    name="security.lock_account",
    description="Lock a user account (prevent login)",
    parameters=[
        ToolParameter(name="user_id", type="string", description="User ID")
    ]
)
def lock_account(user_id: str):
    if not state.get_user(user_id):
        raise ValueError(f"User {user_id} not found")
        
    state.lock_account(user_id)
    state.log_audit({"action": "security.lock_account", "target": user_id, "by": "agent"})
    return {"status": "locked", "user_id": user_id}

@registry.register(
    name="security.unlock_account",
    description="Unlock a user account",
    parameters=[
        ToolParameter(name="user_id", type="string", description="User ID")
    ]
)
def unlock_account(user_id: str):
    if not state.get_user(user_id):
        raise ValueError(f"User {user_id} not found")
        
    state.unlock_account(user_id)
    state.log_audit({"action": "security.unlock_account", "target": user_id, "by": "agent"})
    return {"status": "unlocked", "user_id": user_id}

@registry.register(
    name="security.audit_log",
    description="Fetch recent security audit logs",
    parameters=[
        ToolParameter(name="limit", type="integer", description="Number of entries to fetch")
    ]
)
def audit_log(limit: int = 50):
    return {"logs": state.get_audit_log(limit)}
