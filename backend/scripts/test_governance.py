import sys
import os
import requests
import json
from jose import jwt
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from armoriq.client import gateway, ARMORIQ_SECRET

MCP_URL = "http://localhost:8000"

def test_governance():
    print("🧪 Starting Governance Tests...")

    # 1. Valid Token -> Success
    print("\n1. Testing Valid Token...")
    plan = {
        "steps": [
            {"action": "infra.restart", "params": {"service_id": "auth"}}
        ]
    }
    captured = gateway.capture_plan("test-llm", "restart auth", plan)
    token = gateway.get_intent_token(captured)

    payload = {
        "tool_name": "infra.restart",
        "parameters": {"service_id": "auth"},
        "intent_token": token
    }
    headers = {"X-ArmorIQ-User-Email": "admin_agent"}

    resp = requests.post(f"{MCP_URL}/mcp/tools/execute", json=payload, headers=headers)
    if resp.status_code == 200:
        print("✅ SUCCESS: Valid token accepted")
    else:
        print(f"❌ FAILURE: Valid token rejected: {resp.status_code} {resp.text}")

    # 2. Invalid Token (Bad Secret) -> Blocked
    print("\n2. Testing Invalid Token (Bad Signature)...")
    bad_token = jwt.encode({"sub": "admin_agent", "actions": []}, "wrong-secret", algorithm="HS256")
    payload["intent_token"] = bad_token
    resp = requests.post(f"{MCP_URL}/mcp/tools/execute", json=payload, headers=headers)
    if resp.status_code == 403:
        print("✅ SUCCESS: Bad signature blocked")
    else:
        print(f"❌ FAILURE: Bad signature accepted: {resp.status_code}")

    # 3. Out-of-Scope Action -> Blocked
    print("\n3. Testing Out-of-Scope Action...")
    # Token only allows infra.restart for 'auth'
    payload["tool_name"] = "infra.restart"
    payload["parameters"] = {"service_id": "db"}
    payload["intent_token"] = token # Same token as test 1
    # Wait, token reuse will kick in first if I don't use a new token

    # Let's get a new token for 'auth' and try to use it for 'db'
    token2 = gateway.get_intent_token(captured)
    payload["intent_token"] = token2
    resp = requests.post(f"{MCP_URL}/mcp/tools/execute", json=payload, headers=headers)
    if resp.status_code == 403:
        print("✅ SUCCESS: Out-of-scope action blocked")
    else:
        print(f"❌ FAILURE: Out-of-scope action accepted: {resp.status_code}")

    # 4. Token Reuse -> Blocked
    print("\n4. Testing Token Reuse...")
    # Use token from test 1 again
    payload["parameters"] = {"service_id": "auth"}
    payload["intent_token"] = token
    resp = requests.post(f"{MCP_URL}/mcp/tools/execute", json=payload, headers=headers)
    if resp.status_code == 403:
        print("✅ SUCCESS: Token reuse blocked")
    else:
        print(f"❌ FAILURE: Token reuse accepted: {resp.status_code}")

if __name__ == "__main__":
    # Start MCP in background if not running
    import subprocess
    import time

    print("🚀 Starting MCP for testing...")
    mcp_proc = subprocess.Popen(
        ["uvicorn", "mcp.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd="backend",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)

    try:
        test_governance()
    finally:
        print("\n🛑 Stopping MCP...")
        mcp_proc.terminate()
        mcp_proc.wait()
