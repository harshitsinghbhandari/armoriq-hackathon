import requests
import time
import subprocess
import sys
import os

MCP_URL = "http://localhost:8000"

def wait_for_service(url, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(url)
            return True
        except:
            time.sleep(0.5)
    return False

def verify():
    print("🚀 Starting MCP Verification...")
    
    # Start MCP
    mcp_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mcp.main:app", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    try:
        if not wait_for_service(f"{MCP_URL}/health"):
            print("❌ MCP failed to start")
            return
            
        print("✅ MCP Started")
        
        # 1. Check Meta
        print("🔍 Checking /mcp/meta...")
        resp = requests.get(f"{MCP_URL}/mcp/meta")
        if resp.status_code == 200:
            data = resp.json()
            if "mcp_id" in data and "tools" in data:
                print(f"✅ /mcp/meta OK (Tools: {len(data['tools'])})")
            else:
                print(f"❌ /mcp/meta invalid schema: {data}")
        else:
             print(f"❌ /mcp/meta failed: {resp.status_code}")

        # 2. Check Tools List
        print("🔍 Checking /mcp/tools/list...")
        resp = requests.post(f"{MCP_URL}/mcp/tools/list")
        if resp.status_code == 200:
            data = resp.json()
            if "tools" in data:
                print(f"✅ /mcp/tools/list OK")
            else:
                 print(f"❌ /mcp/tools/list invalid schema: {data}")
        else:
             print(f"❌ /mcp/tools/list failed: {resp.status_code}")
             
        # 3. Check Execute (Missing Token)
        print("🔍 Checking /mcp/tools/execute (Auth Check)...")
        resp = requests.post(f"{MCP_URL}/mcp/tools/execute", json={
            "tool_name": "infra.restart",
            "parameters": {"service_id": "foo"},
            "intent_token": ""
        })
        if resp.status_code == 401:
            print("✅ Auth Check OK (401 on missing token)")
        else:
            print(f"❌ Auth Check Failed: Got {resp.status_code}")

    except Exception as e:
        print(f"❌ Verification Exception: {e}")
    finally:
        mcp_proc.terminate()
        mcp_proc.wait()
        print("🛑 MCP Stopped")

if __name__ == "__main__":
    verify()
