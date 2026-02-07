# System Internal Documentation

**Audience:** Project Contributors, Maintainers, and Reviewers.
**Goal:** Technical deep-dive into the Autonomous Sysadmin Agent architecture and ArmorIQ governance integration.

## 1. System Overview

This system allows an AI agent to autonomously manage infrastructure while being strictly governed by the **ArmorIQ** policy engine. Unlike standard "human-in-the-loop" systems, this implements **"policy-in-the-loop"** enforcement where the infrastructure itself (MCP) rejects any action not accompanied by a valid cryptographic intent token from ArmorIQ.

### High-Level Data Flow

The system operates in a continuous control loop:

1.  **Inject Fault:** `insert_issues.py` creates alerts (e.g., service stop, high CPU) in MCP.
2.  **Sense:** `orchestrator` polls MCP state and feeds it to the `agent`.
3.  **Plan:** `agent` (Ollama) analyzes the state and outputs a JSON plan (`infra.restart`).
4.  **Govern:** `orchestrator` submits the plan to **ArmorIQ** (`capture_plan`).
    *   ArmorIQ checks policies.
    *   If approved, it returns an **Intent Token**.
5.  **Act:** `orchestrator` calls the `mcp` endpoint (`/restart`) with the **Intent Token**.
6.  **Enforce:** `mcp` verifies the token (and its signature/claims) before executing.

## 2. Module Responsibilities

### `agent/`
*   **Role:** Intelligence Layer.
*   **Tech:** FastAPI, Ollama (local LLM).
*   **Key Files:**
    *   `server.py`: Exposes `/run` endpoint. Accepts prompt, returns JSON plan.
    *   `llm.py`: Handles Ollama API communication and schema enforcement (ensures JSON output).
    *   `prompts.py`: System prompts defining the agent's persona and available tools.

### `armoriq/`
*   **Role:** Governance Gateway.
*   **Tech:** ArmorIQ SDK (or Mock).
*   **Key Files:**
    *   `client.py`: Singleton wrapper around the ArmorIQ SDK. Handles the lifecycle of plan capture and token retrieval.
    *   **Mock Mode:** If `USE_MOCK_ARMORIQ=true`, it bypasses the real API and issues "mock-intent-tokens".

### `mcp/` (Mini Cloud Platform)
*   **Role:** Infrastructure Simulator & Enforcement Point.
*   **Tech:** FastAPI.
*   **Key Files:**
    *   `infra.py`: Service management endpoints (`/mcp/infra/restart`). **Protected**.
    *   `alerts.py`: Alert management (`/mcp/alerts/resolve`). **Protected**.
    *   `main.py`: Entry point. Mounts routers.
*   **Security:** Critical endpoints depend on `verify_armoriq`, which checks for `X-ArmorIQ-Intent-ID`.

### `orchestrator/`
*   **Role:** The "Hands" (Runner).
*   **Tech:** Python script (`runner.py`).
*   **Function:**
    *   Connects all components.
    *   Polls state -> Calls Agent -> Calls ArmorIQ -> Calls MCP.
    *   **Stateless:** Does not maintain internal state between cycles.

## 3. ArmorIQ Lifecycle

The governance flow is strict. The orchestrator must follow this sequence for *every* mutating action:

1.  **`capture_plan(llm, prompt, plan)`**
    *   Sends the raw prompt (context) and the agent's proposed JSON plan to ArmorIQ.
    *   ArmorIQ logs this attempt.
2.  **`get_intent_token(plan_id)`**
    *   ArmorIQ evaluates the plan against active Policies.
    *   **Result:** returns a signed JWT-like **Intent Token** binding the specific action (`infra.restart`) and parameters (`service_id=web`) to this approval.
3.  **`invoke(mcp, action, intent_token, ...)`**
    *   The orchestrator passes this token to the MCP.
    *   The MCP verifies the token is valid and matches the requested action.

## 4. Mock vs. Real ArmorIQ

To facilitate local development without hitting the production ArmorIQ API, we support a **Mock Mode**.

*   **Enable:** Set `USE_MOCK_ARMORIQ=true` in `.env` or if API keys are missing.
*   **Behavior:**
    *   `capture_plan`: Returns a dummy ID.
    *   `get_intent_token`: Returns "mock-intent-token-xyz".
    *   `invoke`: Calls MCP directly (MCP must be configured to accept mock tokens, or simply validates presence).
*   **Warning:** Mock mode provides **NO** real security. Do not use in production.

## 5. Policy Management

*   **Real Mode:** Policies are defined in the ArmorIQ SaaS Dashboard.
*   **Local/Mock:** Simple policy logic is mimicked in `policy/engine.py` (though currently largely bypassed or used by the local mock verification if enabled).
*   **Enforcement:** The ultimate enforcement is the **existence** of a valid token. If ArmorIQ declined the plan, no token exists, and MCP rejects the request.

## 6. How to Add New Tools

1.  **MCP:** Implement the endpoint in `mcp/` (e.g., `mcp/data.py: /backup`). Ensure it asks for `X-ArmorIQ-Intent-ID`.
2.  **Agent:** Update `agent/prompts.py` to tell the LLM about the new tool (`data.backup`).
3.  **Policy:** Update ArmorIQ rules to allow this action for the agent.

## 7. Debugging Failures

### Logs
*   **Agent:** `agent_server.log`. Check here if the LLM is outputting invalid JSON.
*   **MCP:** `mcp_server.log`. Check here for `401 Unauthorized` (Token issues) or `500 Server Error`.
*   **Orchestrator:** Stdout. usage: `tail -f agent_server.log`.

### Common Failure Modes
*   **"Unauthorized: ArmorIQ Intent Required"**: The orchestrator tried to call MCP directly without going through ArmorIQ first.
*   **"Identity Mismatch"**: The agent ID in the plan doesn't match the authenticated user.
*   **"Service not found"**: The agent hallucinated a service ID.

## 8. Audit & Security Goals

*   **Audit Log:** MCP logs every action to `audit.log`. This file is the "proof of work" for compliance.
*   **Assumptions:**
    *   The `agent` is untrusted (can hallucinate or be jailbroken).
    *   The `orchestrator` is dumb (just passes messages).
    *   **ArmorIQ** is the Root of Trust.
    *   **MCP** is the Policy Enforcement Point (PEP).

## 9. Common Mistakes

*   **Modifying `.env` but not restarting:** Services load config on startup.
*   **Changing Prompts without testing:** The LLM might stop producing valid JSON.
*   **Forgetting `verify_armoriq`:** If you add an MCP endpoint without this dependency, the agent can bypass governance. **Always add authentication dependencies.**
