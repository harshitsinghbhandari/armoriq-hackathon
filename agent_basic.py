import os
import json
import time
import requests
from google import genai
import dotenv
import re

dotenv.load_dotenv()


# ---------------- CONFIG ---------------- #
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-2.5-flash"

# MCP & Keycloak Configuration
MCP_BASE_URL = "http://localhost:8000"
KEYCLOAK_URL = "http://localhost:8080"
REALM = "hackathon"
CLIENT_ID = "mcp-client"

# Bot Credentials
BOT_USER = os.getenv("MCP_USER", "admin_agent")
BOT_PASS = os.getenv("MCP_PASSWORD", "adminpass")


# ---------------- AUTH ---------------- #

def get_access_token() -> str:
    """Authenticates with Keycloak and returns a bearer token."""
    url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    data = {
        "client_id": CLIENT_ID,
        "username": BOT_USER,
        "password": BOT_PASS,
        "grant_type": "password"
    }

    try:
        resp = requests.post(url, data=data, timeout=5)
        resp.raise_for_status()
        return resp.json()["access_token"]
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        raise


# ---------------- MCP API ---------------- #

def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def get_services(token: str) -> list:
    """Fetch live services from MCP."""
    try:
        url = f"{MCP_BASE_URL}/mcp/infra/list"
        resp = requests.get(url, headers=get_headers(token), timeout=5)
        resp.raise_for_status()
        return resp.json().get("services", [])
    except Exception as e:
        print(f"⚠️ Failed to fetch services: {e}")
        return []

def get_alerts(token: str) -> list:
    """Fetch open alerts from MCP."""
    try:
        url = f"{MCP_BASE_URL}/mcp/alerts/"
        resp = requests.get(url, params={"status": "open"}, headers=get_headers(token), timeout=5)
        resp.raise_for_status()
        return resp.json().get("alerts", [])
    except Exception as e:
        print(f"⚠️ Failed to fetch alerts: {e}")
        return []

def restart_service(token: str, service_id: str):
    """Restart a service via MCP."""
    url = f"{MCP_BASE_URL}/mcp/infra/restart"
    payload = {
        "agent_id": BOT_USER,
        "service_id": service_id
    }
    
    try:
        resp = requests.post(url, json=payload, headers=get_headers(token), timeout=5)
        resp.raise_for_status()
        print(f"✅ Restart Success: {resp.json()['message']}")
    except Exception as e:
        print(f"❌ Restart Failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")

def resolve_alert(token: str, alert_id: str, note: str = "Resolved by AI agent"):
    """Resolve an alert via MCP."""
    url = f"{MCP_BASE_URL}/mcp/alerts/resolve"
    payload = {
        "agent_id": BOT_USER,
        "alert_id": alert_id,
        "resolution_note": note
    }

    try:
        resp = requests.post(url, json=payload, headers=get_headers(token), timeout=5)
        resp.raise_for_status()
        print(f"✅ Alert Resolved: {resp.json()['message']}")
    except Exception as e:
        print(f"❌ Resolve Failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")


# ---------------- LLM HELPER ---------------- #

def extract_json(text: str) -> str:
    """Extract first JSON object from model output."""
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in output")
    return match.group(0)

def build_prompt(services, alerts):
    state_summary = {
        "services": {s["id"]: s["status"] for s in services},
        "alerts": [{"id": a["id"], "msg": a["msg"], "severity": a["severity"]} for a in alerts]
    }

    return f"""
You are a sysadmin AI assistant.

Current system state:
{json.dumps(state_summary, indent=2)}

Your job:
Decide the best next administrative action.

Rules:
- Only choose from:
  - infra.restart (requires 'service_id')
  - alert.resolve (requires 'alert_id')
  - do_nothing
- Prioritize CRITICAL alerts.
- Be conservative.
- Output ONLY valid JSON.

Return exactly this format:
{{
  "action": "<action>",
  "params": {{ ... }},
  "reason": "<short explanation>"
}}
"""


# ---------------- AGENT ---------------- #

def run_agent():
    print("🚀 Starting Agent...")

    # 1. Authenticate
    try:
        token = get_access_token()
        print("🔑 Authenticated with Keycloak")
    except:
        return

    # 2. Get System State
    services = get_services(token)
    alerts = get_alerts(token)
    
    print(f"📊 State: {len(services)} services, {len(alerts)} active alerts")

    # 3. Consult LLM
    prompt = build_prompt(services, alerts)
    
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        text = response.text.strip()
        clean_json = extract_json(text)
        intent = json.loads(clean_json)
        
        print("\n--- DECISION ---")
        print(json.dumps(intent, indent=2))

    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return

    # 4. Execute Action
    action = intent.get("action")
    params = intent.get("params", {})

    print("\n--- EXECUTION ---")
    if action == "infra.restart":
        sid = params.get("service_id")
        if sid:
            print(f"🔄 Restarting service: {sid}...")
            restart_service(token, sid)
        else:
            print("❌ Missing service_id for restart")

    elif action == "alert.resolve":
        aid = params.get("alert_id")
        if aid:
            print(f"✅ Resolving alert: {aid}...")
            resolve_alert(token, aid)
        else:
            print("❌ Missing alert_id for resolve")

    elif action == "do_nothing":
        print("💤 Doing nothing.")

    else:
        print(f"❓ Unknown action: {action}")


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    run_agent()
