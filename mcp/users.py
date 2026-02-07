"""
Users module for the Mini Cloud Platform Simulator.
Handles user management operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from auth.server import get_current_user
from pydantic import BaseModel
from typing import Literal

from system.state import state
from system.logger import log_action
from policy.engine import allow

router = APIRouter(prefix="/mcp/users", tags=["users"])


# ----- Request Models -----
class CreateUserRequest(BaseModel):
    agent_id: str
    user_id: str
    name: str
    email: str
    role: Literal["superadmin", "admin", "junior", "readonly"] = "junior"


class RevokeUserRequest(BaseModel):
    agent_id: str
    user_id: str


class ChangeRoleRequest(BaseModel):
    agent_id: str
    user_id: str
    new_role: Literal["superadmin", "admin", "junior", "readonly"]


class ResetPasswordRequest(BaseModel):
    agent_id: str
    user_id: str


# ----- Response Model -----
class ActionResponse(BaseModel):
    status: str
    message: str


# ----- Endpoints -----
@router.post("/create", response_model=ActionResponse)
def create_user(req: CreateUserRequest, current_user: dict = Depends(get_current_user)):
    """Create a new user."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "user.create", {
        "target_user": req.user_id,
        "agent_id": req.agent_id
    })
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")
    
    if state.get_user(req.user_id):
        raise HTTPException(status_code=400, detail="User already exists")
    
    state.add_user(req.user_id, {
        "name": req.name,
        "email": req.email,
        "role": req.role,
    })
    
    # Consume Quota (Rate Limiting) - though not used for users yet, good practice
    from policy.engine import consume_quota
    consume_quota(current_user, "user.create", {
        "target_user": req.user_id,
        "agent_id": req.agent_id
    })
    
    log_action("user.created", user=current_user["username"], target_user=req.user_id, role=req.role)
    
    return ActionResponse(
        status="success",
        message=f"User '{req.user_id}' created with role '{req.role}'"
    )


@router.post("/revoke", response_model=ActionResponse)
def revoke_user(req: RevokeUserRequest, current_user: dict = Depends(get_current_user)):
    """Revoke (delete) a user."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "user.revoke", {
        "target_user": req.user_id,
        "agent_id": req.agent_id
    })
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")
    
    if not state.get_user(req.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    
    state.delete_user(req.user_id)
    
    from policy.engine import consume_quota
    consume_quota(current_user, "user.revoke", {
        "target_user": req.user_id,
        "agent_id": req.agent_id
    })
    
    log_action("user.revoked", user=current_user["username"], target_user=req.user_id)
    
    return ActionResponse(
        status="success",
        message=f"User '{req.user_id}' has been revoked"
    )


@router.post("/change-role", response_model=ActionResponse)
def change_role(req: ChangeRoleRequest, current_user: dict = Depends(get_current_user)):
    """Change a user's role."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "user.change_role", {
        "target_user": req.user_id, 
        "new_role": req.new_role,
        "agent_id": req.agent_id
    })
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")
    
    user = state.get_user(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_role = user.get("role", "unknown")
    state.update_user(req.user_id, {"role": req.new_role})
    
    from policy.engine import consume_quota
    consume_quota(current_user, "user.change_role", {
        "target_user": req.user_id, 
        "new_role": req.new_role,
        "agent_id": req.agent_id
    })
    
    log_action("user.role_changed", user=current_user["username"], target_user=req.user_id, 
               old_role=old_role, new_role=req.new_role)
    
    return ActionResponse(
        status="success",
        message=f"User '{req.user_id}' role changed from '{old_role}' to '{req.new_role}'"
    )


@router.post("/reset-password", response_model=ActionResponse)
def reset_password(req: ResetPasswordRequest, current_user: dict = Depends(get_current_user)):
    """Reset a user's password (simulated)."""
    # Enforce Identity Binding
    if req.agent_id != current_user["username"]:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    allowed, reason = allow(current_user, "user.reset_password", {
        "target_user": req.user_id,
        "agent_id": req.agent_id
    })
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Policy denied: {reason}")
    
    user = state.get_user(req.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Simulated password reset - just log it
    log_action("user.password_reset", user=current_user["username"], target_user=req.user_id)
    
    return ActionResponse(
        status="success",
        message=f"Password reset for user '{req.user_id}'"
    )


# ----- Utility Endpoints -----
@router.get("/list")
def list_users():
    """List all users."""
    return {"users": list(state.get_users().values())}


@router.get("/{user_id}")
def get_user(user_id: str):
    """Get a specific user."""
    user = state.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
