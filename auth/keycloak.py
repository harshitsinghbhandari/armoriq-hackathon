import os
import requests
import dotenv

dotenv.load_dotenv()

KEYCLOAK_URL = "http://localhost:8080"
REALM = "hackathon"
CLIENT_ID = "mcp-client"

# Bot Credentials
BOT_USER = os.getenv("MCP_USER", "admin_agent")
BOT_PASS = os.getenv("MCP_PASSWORD", "adminpass")

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
