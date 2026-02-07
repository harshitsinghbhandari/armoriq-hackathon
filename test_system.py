"""
Test script for Mini Cloud Platform Simulator.
Calls several MCP endpoints to demo functionality.

Run with: python test_system.py
(Make sure the server is running: uvicorn main:app --reload)
"""

import requests

BASE_URL = "http://localhost:8000"


def call(method: str, endpoint: str, data: dict = None):
    """Helper to make API calls and print results."""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"{method.upper()} {endpoint}")
    
    if method == "get":
        resp = requests.get(url)
    else:
        resp = requests.post(url, json=data)
        print(f"Request: {data}")
    
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    return resp.json()


def main():
    print("=" * 60)
    print("Mini Cloud Platform Simulator - Test Script")
    print("=" * 60)
    
    # 1. List initial state
    print("\n>>> INITIAL STATE")
    call("get", "/mcp/users/list")
    call("get", "/mcp/infra/list")
    call("get", "/mcp/data/list")
    call("get", "/mcp/alerts/")
    
    # 2. Create an alert
    print("\n>>> CREATE ALERT")
    call("post", "/mcp/alerts/create", {
        "agent_id": "root",
        "type": "cpu",
        "msg": "High CPU usage detected on auth service",
        "severity": "high",
        "resource_id": "auth",
    })
    
    # 3. Restart a service
    print("\n>>> RESTART SERVICE")
    call("post", "/mcp/infra/restart", {
        "agent_id": "root",
        "service_id": "auth",
    })
    
    # 4. Scale a service
    print("\n>>> SCALE SERVICE")
    call("post", "/mcp/infra/scale", {
        "agent_id": "root",
        "service_id": "payments",
        "replicas": 3,
    })
    
    # 5. Backup database
    print("\n>>> BACKUP DATABASE")
    call("post", "/mcp/data/backup", {
        "agent_id": "root",
        "db_id": "prod_db",
        "backup_name": "pre_purge_backup",
    })
    
    # 6. Purge database
    print("\n>>> PURGE DATABASE")
    call("post", "/mcp/data/purge", {
        "agent_id": "root",
        "db_id": "prod_db",
        "confirm": True,
    })
    
    # 7. Restore database
    print("\n>>> RESTORE DATABASE")
    call("post", "/mcp/data/restore", {
        "agent_id": "root",
        "db_id": "prod_db",
        "backup_name": "pre_purge_backup",
    })
    
    # 8. Create a new user
    print("\n>>> CREATE USER")
    call("post", "/mcp/users/create", {
        "agent_id": "root",
        "user_id": "charlie",
        "name": "Charlie",
        "email": "charlie@platform.local",
        "role": "junior",
    })
    
    # 9. Change user role
    print("\n>>> CHANGE USER ROLE")
    call("post", "/mcp/users/change-role", {
        "agent_id": "root",
        "user_id": "charlie",
        "new_role": "admin",
    })
    
    # 10. Revoke user
    print("\n>>> REVOKE USER")
    call("post", "/mcp/users/revoke", {
        "agent_id": "root",
        "user_id": "charlie",
    })
    
    # 11. Resolve the alert
    print("\n>>> RESOLVE ALERT")
    call("post", "/mcp/alerts/resolve", {
        "agent_id": "root",
        "alert_id": "alert_1",
        "resolution_note": "Restarted auth service",
    })
    
    # Final state
    print("\n>>> FINAL STATE")
    call("get", "/mcp/users/list")
    call("get", "/mcp/infra/list")
    call("get", "/mcp/data/list")
    call("get", "/mcp/alerts/")
    
    print("\n" + "=" * 60)
    print("Test complete! Check audit.log for logged actions.")
    print("=" * 60)


if __name__ == "__main__":
    main()
