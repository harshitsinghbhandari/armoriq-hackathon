"""
Mini Cloud Platform Simulator - Main Application
Refactored to strictly follow ArmorIQ MCP Specification.
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
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

def verify_armoriq_token(intent_token: str):
    """
    Simulates validation of the ArmorIQ Intent Token.
    In a real scenario, this would verify the JWT signature and claims.
    """
    if not intent_token or intent_token == "invalid-token":
         # Simple check for demo/test purposes
         # Real validation would check issuer, audience, and signature
         return False
    return True

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
def execute_tool(req: ExecuteRequest):
    """
    Executes a tool.
    Strictly token-gated by ArmorIQ intent_token.
    """
    # 1. Validate Token
    if not req.intent_token:
        logger.warning("Execute attempt without intent token")
        raise HTTPException(status_code=401, detail="Missing ArmorIQ Intent Token")
        
    if not verify_armoriq_token(req.intent_token):
        logger.warning(f"Invalid intent token: {req.intent_token}")
        raise HTTPException(status_code=403, detail="Invalid ArmorIQ Intent Token")

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
