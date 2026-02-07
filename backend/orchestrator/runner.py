import time
import json
import os
import requests
import logging
from auth import keycloak
from armoriq.client import gateway
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
        return [], []

def call_agent(prompt: str) -> dict:
    """
    Call the Agent API to get a plan. 
    NOTE: The updated agent server now handles full execution if called with /run!
    However, the orchestrator loop here intends to govern the process itself.
    If we call /run, it might doubly execute.
    
    Decision: The Agent API (`server.py`) now does the full loop for Frontend requests.
    The Orchestrator (`runner.py`) is an alternative "Background Runner".
    To avoid double execution, `runner.py` should perhaps JUST get the plan? 
    But `server.py` `run_agent` does everything. 
    
    If we want `runner.py` to be the governor, we need the Agent to exposes a `plan` endpoint ONLY.
    But `server.py` implementation just now collapsed it all into `/run`.
    
    For the hackathon demo, `runner.py` is likely the "Background Loop".
    If `runner.py` calls `/run`, `server.py` will execute the plan.
    So `runner.py` just needs to trigger it and log the result.
    
    Refactoring runner.py to be a simple trigger for the agent's autonomous cycle.
    """
    try:
        logger.info(f"Triggering Autonomous Agent Cycle via {AGENT_API_URL}...")
        resp = requests.post(
            f"{AGENT_API_URL}/run",
            json={"input": prompt},
            headers={"X-API-Key": AGENT_API_KEY},
            timeout=60 # Extended timeout for full execution
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Agent API call failed: {e}")
        return {"status": "error", "error": str(e)}

def execute_cycle():
    """
    Executes one agent cycle. 
    Since `agent/server.py` now handles the Plan->Govern->Execute loop,
    this orchestrator simply triggers that process based on current state.
    """
    start_time = time.time()
    cycle_id = f"cycle-{int(start_time)}"
    
    logger.info(f"Starting Cycle {cycle_id}")

    # 1. Sense (Just for logging here, agent re-senses)
    try:
        token = keycloak.get_access_token()
        services, alerts = get_state(token)
        logger.info(f"State: {len(services)} services, {len(alerts)} alerts")
        
        state_summary = {
            "services": {s["id"]: s["status"] for s in services},
            "alerts": [{"id": a["id"], "msg": a["msg"], "severity": a["severity"]} for a in alerts]
        }
    except Exception as e:
        logger.error(f"State sensing failed: {e}")
        state_summary = "Unknown - Sensing Failed"

    # 2. Trigger Agent
    # We pass the high-level goal. The Agent service will fetch fresh state and execute.
    result = call_agent("Fix any critical issues in the system.")
    
    logger.info(f"Cycle Result: {result.get('status')}")
    if result.get("results"):
        for res in result["results"]:
            logger.info(f"  Action: {res['action']} -> {res['status']}")

    return result

if __name__ == "__main__":
    execute_cycle()
