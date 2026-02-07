# ArmorIQ: Governed AI Sysadmin

> **Autonomous Infrastructure Management with Secure Governance**

ArmorIQ is a governed AI sysadmin assistant that combines the reasoning power of Gemini with strict policy enforcement, Keycloak IAM, and secure MCP servers. It provides a closed-loop system for detecting, analyzing, and resolving infrastructure issues autonomously, while ensuring every action is authorized and audited.

## Problem Solved
Traditional AI agents often lack the safety guardrails needed for production infrastructure. ArmorIQ solves this by wrapping a reasoning agent in a secure execution environment where:
*   **Identity is enforced:** The agent must authenticate like any other user.
*   **Policy is code:** Actions are checked against a centralized policy engine before execution.
*   **Audit is immutable:** Every decision and action is logged for accountability.

## High-Level Architecture

```
graph TD
    User[Admin / Simulator] -->|Injects Issues| MCP[Secure MCP Server]
    Agent[Gemini Agent] -->|Auth (Keycloak)| MCP
    MCP -->|Enforce Policy| Policy[Policy Engine]
    MCP -->|Log Action| Audit[Audit Log]
    Agent -->|Read State| MCP
    Agent -->|Execute Action| MCP
```

## Key Governance Guarantees
1.  **Identity Binding:** All actions are tied to a verified Keycloak identity.
2.  **Role-Based Access:** The agent operates within strict role limits (e.g., can restart services but cannot delete data).
3.  **Audit Trail:** Comprehensive logging of all API calls, policy decisions, and agent actions.
4.  **Human-in-the-Loop Ready:** Designed to escalate ambiguity or high-risk actions (future scope).

## Autonomous Agent Workflow
1.  **Monitor:** The agent polls the MCP server for system state (services, alerts).
2.  **Reason:** Gemini 2.5 Flash analyzes the state to determine the root cause and optimal recovery action.
3.  **Decide:** The agent formulates a plan (e.g., restart service, resolve alert) and outputs structured JSON.
4.  **Act:** The agent executes the plan via authenticated API calls to the MCP server.
5.  **Verify:** The MCP server validates the action against the policy engine before execution.

## Demo Instructions

### Prerequisites
*   Python 3.10+
*   Java 17+ (Required for Keycloak)
*   Keycloak 26.0.0+ (Local installation)
*   Gemini API Key

### Setup
### Setup

1.  **Clone the repository.**
2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    # Or manually:
    # pip install google-genai python-dotenv requests uvicorn fastapi
    ```
3.  **Set up Keycloak:**
    *   Download Keycloak from [keycloak.org](https://www.keycloak.org/downloads).
    *   Extract the archive to a known location (e.g., `~/keycloak`).
    *   Import the realm and start Keycloak:
        ```bash
        # Make the setup script executable
        chmod +x keycloak/setup_keycloak.sh

        # Run the setup script with the path to your Keycloak directory
        ./keycloak/setup_keycloak.sh /path/to/keycloak-26.0.0
        ```
    *   *Note: This script imports `keycloak/hackathon-realm.json` and starts Keycloak in dev mode on port 8080.*

4.  **Set up environment variables:**
    *   Copy `.env.example` to `.env`:
        ```bash
        cp keycloak/.env.example .env
        ```
    *   Edit `.env` and add your `GEMINI_API_KEY`.
    *   Ensure `MCP_USER` and `MCP_PASSWORD` match the credentials in Keycloak (default in realm: `admin_agent` / `adminpass`).

    ```bash
    GEMINI_API_KEY=your_key_here
    MCP_USER=admin_agent
    MCP_PASSWORD=adminpass
    ```

### Running the Demo
1.  **Start the MCP Server:**
    ```bash
    uvicorn main:app --reload
    ```
2.  **Start the Outcome Simulator (in a new terminal):**
    ```bash
    python insert_issues.py storm 5
    ```
    *This creates a "storm" of 5 random alerts.*
3.  **Run the Agent:**
    ```bash
    python agent_basic.py
    ```
    *Watch the agent authenticate, analyze the alerts, and autonomously resolve them.*

### Verification
1.  **Keycloak:** Open [http://localhost:8080](http://localhost:8080). You should see the Keycloak welcome page.
2.  **MCP Server:** Open [http://localhost:8000/docs](http://localhost:8000/docs). You should see the FastAPI Swagger UI.
3.  **Agent:** The agent script should output "Authentication successful" and then proceed to list alerts.

## Reproducing the Environment on a New Machine

Follow these step-by-step instructions to set up the complete ArmorIQ environment from scratch:

1.  **System Requirements:**
    *   Ensure Java 17+ is installed (`java -version`).
    *   Ensure Python 3.10+ is installed (`python3 --version`).

2.  **Keycloak Installation:**
    *   Download Keycloak (e.g., 26.0.0) zip/tar.gz.
    *   Extract it: `tar -xvzf keycloak-26.0.0.tar.gz`.

3.  **Project Setup:**
    *   `git clone <repo_url>`
    *   `cd armoriq-hackathon`
    *   `pip install -r requirements.txt`

4.  **Configure Identity (Keycloak):**
    *   Run: `./keycloak/setup_keycloak.sh <path_to_extracted_keycloak>`
    *   This script automatically:
        *   Imports the `hackathon` realm from `keycloak/hackathon-realm.json`.
        *   Creates the necessary clients and users (`admin_agent`).
        *   Starts Keycloak in development mode.

5.  **Configure Secrets:**
    *   Create `.env` file.
    *   Add `GEMINI_API_KEY`.
    *   Verify `MCP_USER`/`MCP_PASSWORD` against Keycloak user (if you changed them).

6.  **Launch:**
    *   Terminal 1 (Keycloak): Already running from step 4 or run `$KEYCLOAK_HOME/bin/kc.sh start-dev`.
    *   Terminal 2 (MCP): `uvicorn main:app --reload`.
    *   Terminal 3 (Sim): `python insert_issues.py storm 3`.
    *   Terminal 4 (Agent): `python agent_basic.py`.

## Tech Stack
*   **AI:** Google Gemini 2.5 Flash
*   **Backend:** FastAPI / Python
*   **Auth:** Keycloak (OpenID Connect)
*   **Protocol:** Model Context Protocol (MCP) concepts
*   **Governance:** Custom Policy Engine

## Team
*  Arhan Khade
*  Adit Prabhu
*  Atharv Shetwe
*  Harshit Singh Bhandari

