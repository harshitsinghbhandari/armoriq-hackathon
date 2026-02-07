import unittest
import subprocess
import time
import requests
import os
import signal
import sys
from multiprocessing import Process
import uvicorn
from fastapi import FastAPI

# Configuration
MCP_PORT = 8000
AGENT_PORT = 8001
MOCK_AGENT_PORT = 8002
MCP_URL = f"http://localhost:{MCP_PORT}"
AGENT_URL = f"http://localhost:{AGENT_PORT}"

# Mock Agent for negative tests
mock_agent_app = FastAPI()

@mock_agent_app.post("/run")
def mock_run_bad_plan(input: dict):
    return {"goal": "Destroy World", "steps": [{"action": "infra.shutdown", "params": {"service_id": "all"}}]}

@mock_agent_app.post("/run_garbage")
def mock_run_garbage(input: dict):
    return {"error": "I am broken"}

def run_mock_agent():
    uvicorn.run(mock_agent_app, host="0.0.0.0", port=MOCK_AGENT_PORT)

class TestEndToEnd(unittest.TestCase):
    mcp_proc = None
    agent_proc = None
    mock_agent_proc = None

    @classmethod
    def setUpClass(cls):
        print("\n🚀 Starting E2E Test Setup...")
        
        # Determine Python interpreter
        cls.python_cmd = sys.executable
        if os.path.exists("env/bin/python3"):
            cls.python_cmd = "env/bin/python3"

        # Start MCP
        print("   Starting MCP...")
        cls.mcp_proc = subprocess.Popen(
            [cls.python_cmd, "-m", "uvicorn", "main:app", "--port", str(MCP_PORT)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        
        # Start Agent
        print("   Starting Real Agent...")
        cls.agent_proc = subprocess.Popen(
            [cls.python_cmd, "-m", "uvicorn", "agent.server:app", "--port", str(AGENT_PORT)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        
        # Start Mock Agent
        print("   Starting Mock Agent...")
        cls.mock_agent_proc = Process(target=run_mock_agent)
        cls.mock_agent_proc.start()

        # Wait for services
        print("⏳ Waiting for services...")
        cls.wait_for_port(MCP_PORT)
        cls.wait_for_port(AGENT_PORT)
        cls.wait_for_port(MOCK_AGENT_PORT)
        print("✅ Services Ready.")

    @classmethod
    def tearDownClass(cls):
        print("\n🛑 Tearing down services...")
        if cls.mcp_proc: cls.mcp_proc.terminate()
        if cls.agent_proc: cls.agent_proc.terminate()
        if cls.mock_agent_proc: cls.mock_agent_proc.terminate()
        
        # Ensure cleanup
        # subprocess.call(["pkill", "-f", "uvicorn"]) # risky on user machine, rely on terminate

    @staticmethod
    def wait_for_port(port, retries=20):
        for _ in range(retries):
            try:
                requests.get(f"http://localhost:{port}/health", timeout=1)
                return
            except:
                time.sleep(0.5)
        raise RuntimeError(f"Service on port {port} failed to start")

    def test_01_happy_path(self):
        """Test full cycle: Inject Alert -> Orchestrate -> Resolve"""
        print("\n🧪 TEST: Happy Path")
        
        # 1. Inject Alert
        print("   Injecting Alert...")
        headers = {"X-ArmorIQ-User-Email": "tester"}
        resp = requests.post(f"{MCP_URL}/mcp/alerts/create", json={
            "type": "cpu", "msg": "E2E Test Alert", "severity": "high"
        }, headers=headers)
        self.assertEqual(resp.status_code, 200)
        alert_id = resp.json()["alert"]["id"]
        print(f"   Alert Created: {alert_id}")

        # 2. Run Orchestrator (Subprocess)
        print("   Running Orchestrator...")
        env = os.environ.copy()
        env["USE_MOCK_ARMORIQ"] = "true" # Use Mock Governance
        env["MCP_URL"] = MCP_URL
        env["AGENT_URL"] = AGENT_URL
        
        result = subprocess.run(
            [self.python_cmd, "-m", "orchestrator.runner"],
            env=env, capture_output=True, text=True
        )
        
        # 3. Verify Success output
        self.assertIn("Starting Cycle", result.stderr) # Logging goes to stderr often
        # self.assertEqual(result.returncode, 0) # Should exit 0

        # 4. Verify Alert Resolved
        print("   Verifying Resolution...")
        resp = requests.get(f"{MCP_URL}/mcp/alerts/{alert_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "resolved")
        self.assertEqual(data["resolved_by"], "admin_agent") # Default bot email
        print("✅ Happy Path Passed")

    def test_02_bad_plan_handling(self):
        """Test robustness against bad agent plans"""
        print("\n🧪 TEST: Bad Plan Handling")
        
        # 1. Start with clean state (optional, but good)
        
        # 2. Run Orchestrator against Mock Agent
        print("   Running Orchestrator against Mock Agent...")
        env = os.environ.copy()
        env["USE_MOCK_ARMORIQ"] = "true"
        env["MCP_URL"] = MCP_URL
        env["AGENT_URL"] = f"http://localhost:{MOCK_AGENT_PORT}" # Point to bad agent
        
        result = subprocess.run(
            [self.python_cmd, "-m", "orchestrator.runner"],
            env=env, capture_output=True, text=True
        )
        
        # 3. Verify it handled it
        # The mocked agent returns "infra.shutdown" which doesn't exist anymore -> 404
        # Orchestrator should log error but not crash
        print("   Checking logs for failure handling...")
        self.assertIn("Execution Failed", result.stderr)
        print("✅ Bad Plan Handled")

if __name__ == "__main__":
    unittest.main()
