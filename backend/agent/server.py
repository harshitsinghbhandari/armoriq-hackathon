import os
import json
import logging
import requests
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Header, status
from pydantic import BaseModel
from typing import Optional, Dict, List, Any

from .llm import generate_plan
from armoriq.client import gateway
import dotenv

dotenv.load_dotenv()

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent-server")

app = FastAPI(title="ArmorIQ Agent Service")

AGENT_API_KEY = os.getenv("AGENT_API_KEY", "default-insecure-key")
MCP_BASE_URL = os.getenv("MCP_URL", "http://localhost:8000")

async def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")):
    if x_api_key != AGENT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key

class RunRequest(BaseModel):
    input: str # Goal or overriding instruction
    # Optional: could accept state directly, but better to fetch fresh state here

# --- Helper to fetch state ---
def fetch_system_state():
    try:
        # Note: In real scenarios, this should be authenticated.
        # For this setup, we assume internal network or open sensing.
        services = requests.get(f"{MCP_BASE_URL}/mcp/infra/list", timeout=5).json().get("services", [])
        alerts = requests.get(f"{MCP_BASE_URL}/mcp/alerts/?status=open", timeout=5).json().get("alerts", [])
        return {
            "services": {s["id"]: s["status"] for s in services},
            "alerts": [{"id": a["id"], "msg": a["msg"], "severity": a["severity"]} for a in alerts]
        }
    except Exception as e:
        logger.error(f"Failed to fetch state: {e}")
        return {"error": "Failed to fetch state"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ArmorIQ Agent"}

@app.post("/run", dependencies=[Depends(verify_api_key)])
def run_agent(request: RunRequest):
    """
    Full Orchestration Cycle:
    1. Sense (Fetch State)
    2. Plan (LLM)
    3. Govern (ArmorIQ Capture & Token)
    4. Act (MCP Execution)
    """
    logger.info(f"Received Run Request: {request.input}")
    
    # 1. Sense
    state = fetch_system_state()
    prompt = f"Goal: {request.input}\nCurrent system state:\n{json.dumps(state, indent=2)}"
    
    # 2. Plan
    logger.info("Generating Plan...")
    plan = generate_plan(prompt)
    if not isinstance(plan, dict) or not plan.get("steps"):
        return {"status": "no_action", "plan": plan, "state": state}

    # 3. Govern
    logger.info("Submitting to ArmorIQ...")
    try:
        # Capture
        captured_plan = gateway.capture_plan(
            llm="agent-service-001",
            prompt=prompt,
            plan=plan
        )
        
        # Verify Token
        intent_token = gateway.get_intent_token(captured_plan)
        logger.info(f"Intent Approved. Token: {str(intent_token)[:10]}...")
        
    except Exception as e:
        logger.error(f"Governance Failed: {e}")
        return {
            "status": "blocked",
            "plan": plan,
            "error": str(e),
            "governance": "denied"
        }

    # 4. Act
    logger.info("Executing Steps...")
    results = []
    for step in plan.get("steps", []):
        action = step.get("action")
        params = step.get("params", {})
        
        try:
            # Execute via Gateway (Local MCP with Token)
            # Default to configured MCP URL
            res = gateway.invoke(
                mcp=MCP_BASE_URL,
                action=action,
                intent_token=intent_token,
                params=params,
                user_email="admin_agent"
            )
            results.append({"action": action, "status": "success", "output": res})
        except Exception as e:
            logger.error(f"Execution failed for {action}: {e}")
            results.append({"action": action, "status": "failed", "error": str(e)})

    return {
        "status": "completed",
        "plan": plan,
        "governance": "approved",
        "results": results,
        "state_snapshot": state
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
