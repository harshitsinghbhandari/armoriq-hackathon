import time
import json
import os
import requests
import logging
from auth import keycloak
from armoriq import client as armoriq_client
import dotenv

dotenv.load_dotenv()

# structured logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("orchestrator")

# Configuration
MCP_BASE_URL = os.getenv("MCP_URL", "http://localhost:8000")
AGENT_API_URL = os.getenv("AGENT_URL", "http://localhost:8001")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "default-insecure-key")

def get_headers(token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def get_state(token: str):
    """Fetch system state (Services and Alerts) directly from MCP."""
    try:
        # Fetch Services
        # Note: Using requests directly for monitoring/sensing only as per instructions
        # to remove mcp.client dependency. Execution is strictly via ArmorIQ.
        logger.info(f"Fetching state from {MCP_BASE_URL}...")
        services_resp = requests.get(
            f"{MCP_BASE_URL}/mcp/infra/list",
            headers=get_headers(token),
            timeout=5
        )
        services_resp.raise_for_status()
        services = services_resp.json().get("services", [])

        # Fetch Alerts
        alerts_resp = requests.get(
            f"{MCP_BASE_URL}/mcp/alerts/",
            params={"status": "open"},
            headers=get_headers(token),
            timeout=5
        )
        alerts_resp.raise_for_status()
        alerts = alerts_resp.json().get("alerts", [])

        return services, alerts
    except Exception as e:
        logger.error(f"Failed to fetch state: {e}")
        # Return empty state to avoid crashing loop if monitoring fails
        return [], []

def call_agent(prompt: str) -> dict:
    """Call the standalone Agent API to get a plan."""
    try:
        logger.info(f"Calling Agent API at {AGENT_API_URL}...")
        resp = requests.post(
            f"{AGENT_API_URL}/run",
            json={"input": prompt},
            headers={"X-API-Key": AGENT_API_KEY},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Agent API call failed: {e}")
        return {"goal": "Error", "steps": [], "error": str(e)}

def execute_cycle():
    """
    Executes one agent cycle following: State -> Agent -> ArmorIQ -> Result
    """
    start_time = time.time()
    # Unique ID for tracking
    cycle_id = f"cycle-{int(start_time)}"
    
    logger.info(f"Starting Cycle {cycle_id}")
    
    result_log = {
        "cycle_id": cycle_id,
        "timestamp": start_time,
        "status": "pending",
        "stages": {}
    }

    # 1. Authenticate (for state reading)
    try:
        token = keycloak.get_access_token()
        result_log["stages"]["auth"] = "success"
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return {"status": "error", "message": f"Authentication failed: {e}"}

    # 2. Get System State
    services, alerts = get_state(token)
    logger.info(f"State: {len(services)} services, {len(alerts)} alerts")
    
    state_summary = {
        "services": {s["id"]: s["status"] for s in services},
        "alerts": [{"id": a["id"], "msg": a["msg"], "severity": a["severity"]} for a in alerts]
    }
    result_log["stages"]["state"] = state_summary

    # 3. Consult LLM (Agent API)
    # Prepare prompt with state only. 
    # System prompt on server side handles instructions.
    prompt = f"Current system state:\n{json.dumps(state_summary, indent=2)}"
    
    plan = call_agent(prompt)
    
    # Handle potentially malformed plan
    if not isinstance(plan, dict):
        logger.warning(f"Agent returned invalid plan format: {plan}")
        plan = {"goal": "Error", "steps": [], "raw": str(plan)}

    logger.info(f"Plan received with {len(plan.get('steps', []))} steps")
    result_log["stages"]["plan"] = plan

    if not plan.get("steps"):
        logger.info("No steps in plan. Cycle complete.")
        return {"status": "success", "message": "No steps", "log": result_log}

    # 4. Governance (ArmorIQ)
    try:
        logger.info("Submitting plan to ArmorIQ...")
        # Capture Plan
        captured_plan = armoriq_client.gateway.capture_plan(
            llm="agent-service-v1",
            prompt=prompt,
            plan=plan
        )
        
        # Get Intent Token
        intent_token = armoriq_client.gateway.get_intent_token(captured_plan)
        logger.info(f"Intent approved. Token: {intent_token[:8]}...")
        result_log["stages"]["governance"] = "approved"
    except Exception as e:
        logger.error(f"Governance Blocked: {e}")
        result_log["stages"]["governance"] = f"blocked: {e}"
        return {"status": "blocked", "error": str(e), "log": result_log}

    # 5. Execution (via ArmorIQ)
    execution_results = []
    user_email = keycloak.BOT_USER
    
    logger.info("Executing steps via ArmorIQ...")
    for step in plan["steps"]:
        action = step.get("action")
        if not action:
            continue
            
        # Determine MCP URL (default to configured MCP)
        # Plan might return "mcp": "{mcp_base_url}" based on system prompt template
        # We should use our configured URL
        mcp_url = MCP_BASE_URL
        params = step.get("params", {})
        
        step_log = {"action": action, "params": params}
        logger.info(f"Invoking {action} on {mcp_url}")
        
        try:
            # EXECUTE ONLY VIA ARMORIQ
            res = armoriq_client.gateway.invoke(
                mcp=mcp_url,
                action=action,
                intent_token=intent_token,
                params=params,
                user_email=user_email
            )
            logger.info(f"Success: {res}")
            step_log["status"] = "success"
            step_log["output"] = res
        except Exception as e:
            logger.error(f"Execution Failed for {action}: {e}")
            step_log["status"] = "failed"
            step_log["error"] = str(e)
            execution_results.append(step_log)
            # Stop execution on failure
            logger.error("Stopping execution due to failure.")
            break
        
        execution_results.append(step_log)

    result_log["stages"]["execution"] = execution_results
    result_log["status"] = "success"
    
    return result_log

if __name__ == "__main__":
    execute_cycle()
