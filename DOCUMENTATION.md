# System Documentation

This document provides a detailed technical overview of the ArmorIQ system for engineering and development purposes.

## Current System Status
The system is currently in a **functional prototype** state. The core mechanics of agent authentication, state retrieval, policy enforcement, and autonomous action execution are implemented and tested end-to-end.

## Architecture Breakdown

### 1. Gemini Agent (`agent_basic.py`)
- **Role:** The "brain" of the system.
- **Function:**
    - Authenticates against Keycloak to obtain a bearer token.
    - Polls the `infra/list` and `alerts/` endpoints to build a context window.
    - Uses `gemini-2.5-flash` to reason about the state and generate a structured JSON plan.
    - Executes actions (`infra.restart`, `alert.resolve`) via the MCP API.

### 2. Keycloak Auth (`auth.py`)
- **Role:** Identity Provider (IdP).
- **Function:**
    - Issues OpenID Connect (OIDC) tokens.
    - Manages users, roles, and clients.
    - Enforces authentication for all API endpoints.

### 3. Secure MCP Services (`mcp/*.py`)
- **Role:** The "hands" of the system (Model Context Protocol server).
- **Function:**
    - Exposes strict API endpoints for infrastructure management.
    - Validates all incoming requests against the policy engine.
    - Logs all activities to the audit log.

### 4. Policy Engine (`policy/engine.py`)
- **Role:** The "conscience" of the system.
- **Function:**
    - Evaluate every action request *before* execution.
    - Enforces rules like "Agents can only restart services if they own the alert" (future implementation).
    - Currently implements basic allow/deny logic based on role and resource type.

### 5. Simulator (`insert_issues.py`)
- **Role:** Chaos Monkey.
- **Function:**
    - Injects synthetic failures (alerts, service degradations) into the system.
    - Used to test the agent's recovery capabilities.

## Execution Flow (Step-by-Step)

1.  **Issue Injection:** `insert_issues.py` POSTs a new alert to `mcp/alerts/create`.
2.  **State Polling:** `agent_basic.py` loops, requesting `mcp/alerts/` (GET) with its bearer token.
3.  **Reasoning:** The agent constructs a prompt with the current alerts and sends it to Gemini.
4.  **Decision:** Gemini returns a JSON object: `{"action": "infra.restart", "params": {"service_id": "web-01"}}`.
5.  **Action Request:** The agent POSTs to `mcp/infra/restart` with the bearer token.
6.  **Policy Check:** The MCP server interception layer calls `policy.check(action="restart", user="admin_agent")`.
7.  **Execution:** If approved, the service is restarted.
8.  **Audit:** The action and its result are written to `audit.log`.

## Security Model
*   **Zero Trust:** No action is trusted implicitly; all must carry a valid token.
*   **Least Privilege:** The agent account should only have the roles necessary for its function (e.g., `operator`, not `admin`).
*   **Auditability:** Non-repudiation of actions via signed tokens and immutable logs.

## Governance Model
*   **Policy as Code:** Governance rules are defined in Python, not vague documents.
*   **Centralized Enforcement:** The policy engine is the single source of truth for authorization.

## Integration Points (ArmorIQ)
*   **SDK:** The ArmorIQ SDK will replace the current manual `policy/engine.py` logic.
*   **Dashboard:** Future integration will visualize the audit log and policy decisions.

## Known Limitations
*   **No Persistent State:** Alerts and services are in-memory (reset on restart).
*   **Single Agent:** Currently designed for a single active agent process.
*   **Basic Policy:** The current policy engine is a stub and needs expansion.

## Technical Debt
*   Hardcoded credentials in `.env` (should use secrets management).
*   Lack of unit tests for edge cases in the policy engine.
*   `agent_basic.py` uses a simple loop; needs backoff and better error handling.

## Development Setup
See `README.md` for standard setup.

### Warnings (Do Not Break)
*   **Auth Flow:** Do not bypass the `get_current_user` dependency in FastAPI; it breaks the security model.
*   **Audit Logging:** Do not remove the logging calls in the MCP endpoints; they are required for governance.
