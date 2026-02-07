import os
import sys
import requests
import dotenv
import random
import argparse
import time

dotenv.load_dotenv()

# Configuration
MCP_BASE_URL = "http://localhost:8000"
KEYCLOAK_URL = "http://localhost:8080"
REALM = "hackathon"
CLIENT_ID = "mcp-client"

ADMIN_USER = os.getenv("MCP_USER", "admin_agent")
ADMIN_PASS = os.getenv("MCP_PASSWORD", "adminpass")

def get_access_token():
    """Get auth token from Keycloak."""
    url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    payload = {
        "client_id": CLIENT_ID,
        "username": ADMIN_USER,
        "password": ADMIN_PASS,
        "grant_type": "password"
    }
    try:
        resp = requests.post(url, data=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()["access_token"]
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        sys.exit(1)

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def create_high_alert(token):
    """Create a single high severity alert."""
    payload = {
        "agent_id": ADMIN_USER,
        "type": "custom",
        "msg": "Critical system failure detected",
        "severity": "critical"
    }
    resp = requests.post(
        f"{MCP_BASE_URL}/mcp/alerts/create",
        json=payload,
        headers=get_headers(token)
    )
    if resp.status_code == 200:
        print(f"✅ Created HIGH alert: {resp.json()['alert']['id']}")
    else:
        print(f"❌ Failed to create alert: {resp.text}")

def create_alert_storm(token, count):
    """Create N alerts."""
    print(f"🌩️ Starting alert storm ({count})...")
    types = ["cpu", "memory", "network", "disk"]
    severities = ["low", "medium", "high", "critical"]
    
    for i in range(count):
        payload = {
            "agent_id": ADMIN_USER,
            "type": random.choice(types),
            "msg": f"Storm alert #{i+1} - Random failure",
            "severity": random.choice(severities)
        }
        resp = requests.post(
            f"{MCP_BASE_URL}/mcp/alerts/create",
            json=payload,
            headers=get_headers(token)
        )
        if resp.status_code == 200:
            print(f"  - Alert {i+1}/{count} created")
        else:
            print(f"  ❌ Failed alert {i+1}: {resp.text}")
        time.sleep(0.1) 
    print("✅ Alert storm complete.")

def degrade_service(token, service_id):
    """Simulate service degradation via alert."""
    payload = {
        "agent_id": ADMIN_USER,
        "type": "service",
        "msg": f"Service '{service_id}' is degraded (high latency)",
        "severity": "high",
        "resource_id": service_id
    }
    resp = requests.post(
        f"{MCP_BASE_URL}/mcp/alerts/create",
        json=payload,
        headers=get_headers(token)
    )
    if resp.status_code == 200:
        print(f"✅ Service '{service_id}' marked as DEGRADED (Alert created)")
    else:
        print(f"❌ Failed to degrade service: {resp.text}")

def reset_system(token):
    """Resolve all alerts and ensure services are running."""
    print("🔄 Resetting system...")
    
    headers = get_headers(token)

    # 1. Resolve all open alerts
    # Need to fetch all open alerts first
    try:
        alerts_resp = requests.get(f"{MCP_BASE_URL}/mcp/alerts/?status=open", headers=headers)
        alerts_resp.raise_for_status()
        alerts = alerts_resp.json().get("alerts", [])
        print(f"  - Found {len(alerts)} open alerts.")
        
        for alert in alerts:
            res_payload = {
                "agent_id": ADMIN_USER,
                "alert_id": alert["id"],
                "resolution_note": "System Reset"
            }
            requests.post(f"{MCP_BASE_URL}/mcp/alerts/resolve", json=res_payload, headers=headers)
        
        print("  ✅ All alerts resolved.")
    except Exception as e:
        print(f"  ❌ Failed to fetch/resolve alerts: {e}")

    # 2. Restart all services if not running
    # Note: Using '/list' endpoint from previous agent_basic analysis
    try:
        services_resp = requests.get(f"{MCP_BASE_URL}/mcp/infra/list", headers=headers)
        services_resp.raise_for_status()
        services = services_resp.json().get("services", [])
        
        for svc in services:
            if svc.get("status") != "running":
                restart_payload = {
                    "agent_id": ADMIN_USER,
                    "service_id": svc["id"]
                }
                requests.post(f"{MCP_BASE_URL}/mcp/infra/restart", json=restart_payload, headers=headers)
                print(f"  - Restarted {svc['id']}")
    except Exception as e:
        print(f"  ❌ Failed to fetch/restart services: {e}")

    print("✅ System reset complete.")

def main():
    parser = argparse.ArgumentParser(description="Inject issues into MCP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommands
    subparsers.add_parser("alert", help="Create one high severity alert")
    
    storm_parser = subparsers.add_parser("storm", help="Create multiple alerts")
    storm_parser.add_argument("count", type=int, help="Number of alerts")
    
    degrade_parser = subparsers.add_parser("degrade", help="Degrade a service")
    degrade_parser.add_argument("service_id", type=str, help="Service ID")

    subparsers.add_parser("reset", help="Resolve all alerts and fix services")

    args = parser.parse_args()
    
    print("🔑 Authenticating...")
    token = get_access_token()

    if args.command == "alert":
        create_high_alert(token)
    elif args.command == "storm":
        create_alert_storm(token, args.count)
    elif args.command == "degrade":
        degrade_service(token, args.service_id)
    elif args.command == "reset":
        reset_system(token)

if __name__ == "__main__":
    main()
