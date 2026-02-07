import requests
import dotenv

dotenv.load_dotenv()

MCP_BASE_URL = "https://damon-precloacal-dayfly.ngrok-free.dev"

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

def restart_service(token: str, service_id: str, agent_id: str):
    """Restart a service via MCP."""
    url = f"{MCP_BASE_URL}/mcp/infra/restart"
    payload = {
        "agent_id": agent_id,
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

def resolve_alert(token: str, alert_id: str, agent_id: str, note: str = "Resolved by AI agent"):
    """Resolve an alert via MCP."""
    url = f"{MCP_BASE_URL}/mcp/alerts/resolve"
    payload = {
        "agent_id": agent_id,
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
