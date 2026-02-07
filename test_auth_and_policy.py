#!/usr/bin/env python3
"""
MCP Auth + Governance Integration Test
=====================================

Purpose:
  End-to-end verification of:
  - Keycloak authentication
  - JWT validation
  - Role-based authorization
  - Policy enforcement

Run:
  python3 test_auth_and_policy.py

Requirements:
  pip install requests
"""

import requests
import sys
import time


# ---------------- CONFIG ---------------- #

KEYCLOAK_URL = "http://localhost:8080"
REALM = "hackathon"
CLIENT_ID = "mcp-client"

MCP_URL = "http://localhost:8000"

ADMIN_USER = "admin_agent"
ADMIN_PASS = "adminpass"

JUNIOR_USER = "junior_agent"
JUNIOR_PASS = "juniorpass"


# ---------------- HELPERS ---------------- #


def fatal(msg):
    print(f"\n[FATAL] {msg}")
    sys.exit(1)


def get_token(username, password):
    """Fetch OAuth token from Keycloak."""

    url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"

    data = {
        "client_id": CLIENT_ID,
        "username": username,
        "password": password,
        "grant_type": "password"
    }

    try:
        r = requests.post(url, data=data, timeout=10)
        r.raise_for_status()
        return r.json()["access_token"]

    except Exception as e:
        fatal(f"Token fetch failed for {username}: {e}")


def restart(token, agent_id, service="payments"):
    """Call protected restart endpoint."""

    url = f"{MCP_URL}/mcp/infra/restart"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "agent_id": agent_id,
        "service_id": service
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        return r.status_code, r.json()

    except Exception as e:
        return 500, {"error": str(e)}


def print_result(tag, label, code, expect=None):

    ok = False

    if expect == "success" and code == 200:
        ok = True

    elif expect == "blocked" and code == 403:
        ok = True

    elif expect is None:
        ok = True

    status = "PASS" if ok else "FAIL"

    print(f"[{tag}] {label:<25} → {status} (HTTP {code})")

    return ok


# ---------------- TESTS ---------------- #


def run():

    print("\n=== MCP GOVERNANCE TEST ===\n")

    # --------------------------------------------------
    # Fetch Tokens
    # --------------------------------------------------

    print("Fetching tokens...")

    admin_token = get_token(ADMIN_USER, ADMIN_PASS)
    junior_token = get_token(JUNIOR_USER, JUNIOR_PASS)

    print("Tokens acquired.\n")


    # --------------------------------------------------
    # ADMIN TESTS
    # --------------------------------------------------

    print("=== ADMIN TESTS ===")

    code, _ = restart(admin_token, ADMIN_USER, "payments")
    ok1 = print_result("ADMIN", "First restart", code, "success")

    code, _ = restart(admin_token, ADMIN_USER, "payments")
    ok2 = print_result("ADMIN", "Second restart", code, "success")

    if not (ok1 and ok2):
        fatal("Admin behavior incorrect")

    print()


    # --------------------------------------------------
    # JUNIOR TESTS
    # --------------------------------------------------

    print("=== JUNIOR TESTS ===")

    service = "db"   # isolate from admin test

    code, _ = restart(junior_token, JUNIOR_USER, service)
    ok1 = print_result("JUNIOR", "First restart", code, "success")

    code, resp = restart(junior_token, JUNIOR_USER, service)
    ok2 = print_result("JUNIOR", "Second restart", code, "blocked")

    if not ok1:
        fatal("Junior first restart failed")

    if not ok2:
        print("\nPolicy failure response:")
        print(resp)
        fatal("Junior rate-limit NOT enforced")

    print()


    # --------------------------------------------------
    # IDENTITY SPOOF TEST
    # --------------------------------------------------

    print("=== IDENTITY SPOOF TEST ===")

    print("Junior token pretending to be admin...")

    code, resp = restart(
        junior_token,
        ADMIN_USER,        # mismatch
        "auth"
    )

    ok = print_result("SPOOF", "Token/ID mismatch", code, "blocked")

    if not ok:
        print("\nResponse:")
        print(resp)
        fatal("Identity binding NOT enforced")

    print()


    # --------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------

    print("=== SUMMARY ===")
    print("All governance tests PASSED ✅")
    print("System enforces:")
    print(" - Authentication")
    print(" - Role separation")
    print(" - Rate limiting")
    print(" - Identity binding\n")


# ---------------- MAIN ---------------- #

if __name__ == "__main__":

    try:
        run()

    except KeyboardInterrupt:
        print("\nAborted.")
