from .registry import registry, ToolParameter
from system.state import state
import logging

logger = logging.getLogger("mcp.users")

@registry.register(
    name="identity.list",
    description="List all users in the system",
    parameters=[]
)
def list_users():
    return list(state.get_users().values())

@registry.register(
    name="identity.create",
    description="Create a new user account",
    parameters=[
        ToolParameter(name="user_id", type="string", description="Unique User ID"),
        ToolParameter(name="name", type="string", description="Full Name"),
        ToolParameter(name="email", type="string", description="Email Address"),
        ToolParameter(name="role", type="string", description="Role (admin, user, junior)")
    ]
)
def create_user(user_id: str, name: str, email: str, role: str):
    if state.get_user(user_id):
        raise ValueError(f"User {user_id} already exists")
    
    user = {
        "name": name,
        "email": email,
        "role": role,
        "status": "active"
    }
    state.add_user(user_id, user)
    state.log_audit({"action": "identity.create", "target": user_id, "by": "agent"})
    return {"status": "created", "user": user}

@registry.register(
    name="identity.revoke",
    description="Revoke/Delete a user account",
    parameters=[
        ToolParameter(name="user_id", type="string", description="User ID to revoke")
    ]
)
def revoke_user(user_id: str):
    if not state.get_user(user_id):
        raise ValueError(f"User {user_id} not found")
    
    state.delete_user(user_id)
    state.log_audit({"action": "identity.revoke", "target": user_id, "by": "agent"})
    return {"status": "revoked", "user_id": user_id}

@registry.register(
    name="identity.change_role",
    description="Change a user's role",
    parameters=[
        ToolParameter(name="user_id", type="string", description="User ID"),
        ToolParameter(name="new_role", type="string", description="New Role")
    ]
)
def change_role(user_id: str, new_role: str):
    if not state.get_user(user_id):
        raise ValueError(f"User {user_id} not found")
        
    state.update_user(user_id, {"role": new_role})
    state.log_audit({"action": "identity.change_role", "target": user_id, "new_role": new_role, "by": "agent"})
    return {"status": "updated", "user_id": user_id, "new_role": new_role}

@registry.register(
    name="identity.reset_password",
    description="Trigger password reset for a user",
    parameters=[
        ToolParameter(name="user_id", type="string", description="User ID")
    ]
)
def reset_password(user_id: str):
    if not state.get_user(user_id):
        raise ValueError(f"User {user_id} not found")
    
    # Simulate reset
    state.log_audit({"action": "identity.reset_password", "target": user_id, "by": "agent"})
    return {"status": "reset_email_sent", "user_id": user_id}
