"""
Mini Cloud Platform Simulator - Main Application
Refactored to strictly follow ArmorIQ MCP Specification.
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, Set
import os
from jose import jwt, JWTError
import logging

# Standard Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp-server")

from system import logger as audit_logger  # Rename for clarity
from mcp import infra, alerts
from mcp.registry import registry

app = FastAPI(
    title="ArmorIQ MCP Simulator",
    version="1.0.0",
    description="Standardized MCP for ArmorIQ Hackathon"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Read-Only Routers (for Sensing/Monitoring)
app.include_router(infra.router)
app.include_router(alerts.router)

# --- MCP Standard Schemas ---

class ExecuteRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    intent_token: str # ArmorIQ Intent Token

# --- Dependencies ---

ARMORIQ_SECRET = os.getenv("ARMORIQ_SECRET", "demo-secret-key-12345")
# Simple in-memory set to prevent token reuse during the demo
USED_TOKENS: Set[str] = set()

def verify_armoriq_token(intent_token: str, tool_name: str, parameters: Dict[str, Any], user_email: Optional[str] = None):
    """
    Validates the ArmorIQ Intent Token against the requested action and parameters.
    """
    try:
        payload = jwt.decode(intent_token, ARMORIQ_SECRET, algorithms=["HS256"])

        # 1. Check expiration (handled by jwt.decode)

        # 2. Prevent Token Reuse
        jti = payload.get("jti")
        if not jti or jti in USED_TOKENS:
            logger.warning(f"Token reuse or missing JTI: {jti}")
            return False
        USED_TOKENS.add(jti)

        # 3. Prevent User Impersonation
        if user_email and payload.get("sub") != user_email:
            logger.warning(f"User mismatch: {user_email} vs {payload.get('sub')}")
            return False

        # 4. Check Action Binding
        allowed_actions = payload.get("actions", [])
        is_authorized = False

        for allowed in allowed_actions:
            if allowed.get("action") == tool_name:
                # Basic parameter check - ensure requested params match or are a subset of allowed
                allowed_params = allowed.get("params", {})

                # Check if all required parameters match
                match = True
                for k, v in allowed_params.items():
                    if parameters.get(k) != v:
                        match = False
                        break

                if match:
                    is_authorized = True
                    break

        if not is_authorized:
            logger.warning(f"Action {tool_name} not authorized in token")
            return False

        return True
    except JWTError as e:
        logger.error(f"JWT Verification failed: {e}")
        return False

# --- MCP Endpoints ---

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/mcp/meta")
def get_meta():
    """Returns the MCP manifest."""
    return {
        "mcp_id": "mcp-simulator-001",
        "version": "1.0.0",
        "description": "Simulator for Infrastructure and Alerts",
        "tools": registry.list_tools(),
        "scopes": ["infra", "alerts"]
    }

@app.post("/mcp/tools/list")
def list_tools():
    """Returns list of available tools."""
    return {
        "tools": registry.list_tools()
    }

@app.post("/mcp/tools/execute")
def execute_tool(req: ExecuteRequest, x_armoriq_user_email: Optional[str] = Header(None)):
    """
    Executes a tool.
    Strictly token-gated by ArmorIQ intent_token.
    """
    # 1. Validate Token & Binding
    if not req.intent_token:
        logger.warning("Execute attempt without intent token")
        raise HTTPException(status_code=401, detail="Missing ArmorIQ Intent Token")
        
    if not verify_armoriq_token(req.intent_token, req.tool_name, req.parameters, x_armoriq_user_email):
        logger.warning(f"Unauthorized or invalid intent token for {req.tool_name}")
        raise HTTPException(status_code=403, detail="Invalid or unauthorized ArmorIQ Intent Token")

    # 2. Lookup Tool
    tool_func = registry.get_tool(req.tool_name)
    if not tool_func:
        logger.warning(f"Tool not found: {req.tool_name}")
        raise HTTPException(status_code=404, detail=f"Tool '{req.tool_name}' not found")
        
    # 3. Execute
    try:
        logger.info(f"Executing tool '{req.tool_name}' with token {req.intent_token[:8]}...")
        # We pass parameters directly
        result = tool_func(**req.parameters)
        return {
            "status": "success",
            "result": result
        }
    except ValueError as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected execution error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during execution")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting ArmorIQ MCP Simulator (Standard Mode)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
