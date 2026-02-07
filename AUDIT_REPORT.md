# ArmorIQ Governance Audit Report: Autonomous Sysadmin Agent

**Auditor:** Jules (Senior Distributed Systems Architect & Security Reviewer)
**Verdict:** NO-GO / CRITICAL FAILURE
**Date:** 2024-05-20

---

## 1. Actual System Architecture

The system's real runtime flow deviates significantly from the intended design and documented architecture.

### Runtime Flow:
1.  **Orchestrator (`orchestrator/runner.py`)** acts as the central hub.
2.  **Sensing**: The Orchestrator uses a Keycloak-issued token (`auth/keycloak.py`) to poll state from the MCP Simulator.
3.  **Planning**: State is sent to a standalone Agent Service (`agent/server.py`) which wraps Ollama.
4.  **Governance**: The plan is submitted to ArmorIQ (via `armoriq/client.py`) to obtain an "Intent Token."
5.  **Execution**: The Orchestrator calls the MCP's `/mcp/tools/execute` endpoint, passing the Intent Token.

### Trust Boundaries:
*   **Missing Trust**: The MCP Simulator (`mcp/main.py`) does not cryptographically verify the ArmorIQ Intent Token. It uses a string-matching placeholder.
*   **Orchestrator Over-Privilege**: The Orchestrator holds both long-lived Keycloak credentials and short-lived Intent Tokens, making it a high-value target for compromise.
*   **Entry Point Discrepancy**: `run_demo.sh` starts `backend/main.py` (Port 8000), which lacks the execution endpoint defined in `backend/mcp/main.py`.

---

## 2. Intent & Planning Layer

### Generation Analysis:
*   **Method**: Ollama `llama3.2` with a structured system prompt.
*   **Enforcement**: JSON is enforced via prompt instructions and a regex-based `extract_json` helper in `agent/llm.py`.
*   **Weaknesses**:
    *   **Regex Fragility**: The regex `\{.*\}` in `llm.py` is easily broken by nested JSON or adversarial text.
    *   **Incomplete Plans**: The Orchestrator does not validate that the LLM's plan actually addresses the CRITICAL alerts found during the sensing phase.
    *   **Hallucination Risk**: The agent is prompted with available actions but not strictly constrained by a schema-validator during generation.

---

## 3. ArmorIQ Integration Audit

### Integration Status:
*   **`capture_plan` / `get_intent_token`**: Correctly called in the Orchestrator.
*   **`invoke` Routing**: Correctly implemented in the `ArmorIQGateway` wrapper.
*   **Critical Bypass**:
    *   **Mock Mode**: Setting `USE_MOCK_ARMORIQ=true` completely removes the governance layer, returning hardcoded strings that the MCP accepts blindly.
    *   **Fake Integration**: The system "simulates" governance rather than enforcing it.

---

## 4. MCP Enforcement Review

### Identified Vulnerabilities:
*   **Unauthorized Entry**: All mutating tools (`infra.restart`, `alert.resolve`) are reachable via `/mcp/tools/execute`.
*   **Placeholder Validation**: `mcp/main.py:verify_armoriq_token` is a stub:
    ```python
    if not intent_token or intent_token == "invalid-token":
         return False
    return True
    ```
    *Impact: Any string (e.g., "pwned") is accepted as a valid authorization token.*
*   **Missing Scope Checks**: The system does not verify if the token matches the requested tool or parameters.

---

## 5. Role, Permission, Delegation Analysis

### Findings:
*   **Hardcoded Roles**: `SystemState` defines `superadmin`, `admin`, and `junior`, but these are decoupled from the ArmorIQ intent flow.
*   **Privilege Escalation**: Since the MCP doesn't check roles for tool execution, a "junior" authenticated agent can perform any action.
*   **Missing Delegation**: The `TODO.md` mentions a delegation scenario, but the code contains zero implementation for human escalation or fallback.

---

## 6. Data & State Safety

### Risks:
*   **Volatility**: `SystemState` is purely in-memory. A crash or restart wipes all system status and user data.
*   **Integrity Bug**: `SystemState` lacks the `get_alert` method, but `mcp/alerts.py` calls it.
    *   *Result: The system crashes whenever the agent tries to resolve an alert.*

---

## 7. Audit & Traceability

### Evaluation:
*   **Completeness**: Mutating actions are logged to `audit.log`.
*   **Blind Spots**: State reads, authentication attempts, and governance denials are not captured in the local audit log.
*   **Tamper Resistance**: NONE. The audit log is a local JSONL file with no signing or remote replication.

---

## 8. Security Threat Model

| Threat | Exploit | Vulnerable Code | Impact |
| :--- | :--- | :--- | :--- |
| **Prompt Injection** | User provides "goal" to hijack agent logic. | `agent/server.py:run_agent` | Full agent takeover. |
| **Token Replay** | Reusing a previously valid intent token. | `mcp/main.py:verify_armoriq_token` | Unauthorized re-execution. |
| **Internal Bypass** | Disabling ArmorIQ in `.env`. | `armoriq/client.py:__init__` | Total governance bypass. |
| **Identity Mismatch** | Orchestrator impersonating different users. | `orchestrator/runner.py` | Audit log spoofing. |

---

## 9. Compliance With Hackathon Requirements

*   **Separation of Reasoning/Execution**: **PASS** (Agent and MCP are decoupled).
*   **MCP Enforcement**: **FAIL** (Validation is a stub).
*   **Rule-based Governance**: **FAIL** (Mock mode bypasses all rules).
*   **Delegation Scenario**: **FAIL** (Not implemented).

---

## 10. Critical Gaps (Top 10)

1.  **Broken Token Validation**: `verify_armoriq_token` is a stub (Complete Bypass).
2.  **Runtime Crash**: Missing `SystemState.get_alert` method (Crash on Execute).
3.  **Entry Point Mismatch**: `run_demo.sh` runs the wrong main file (404 on Invoke).
4.  **Token-Action Binding**: Token is not bound to specific actions (Over-permissiveness).
5.  **Brittle Plan Extraction**: Regex-based JSON parsing (Unreliable).
6.  **Hardcoded Secrets**: Insecure API keys in code and frontend.
7.  **In-Memory Only State**: No persistence (Data loss).
8.  **Prompt Injection**: Unsanitized user input to Agent.
9.  **RBAC Absence**: Defined roles are ignored during execution.
10. **Tamperable Logs**: Local unprotected audit file.

---

## 11. Refactor & Fix Plan (48h Scope)

### T+0 to T+8h: Survival Fixes
*   Merge `backend/main.py` and `backend/mcp/main.py` or fix `run_demo.sh`.
*   Implement `SystemState.get_alert`.
*   Implement JWT signature verification in `mcp/main.py` using a shared secret or JWKS.

### T+8 to T+24h: Governance Hardening
*   Bind Intent Tokens to specific actions/parameters in the MCP validation logic.
*   Switch Agent extraction to a schema-validated parser (e.g., Pydantic).
*   Implement role-based tool restrictions in `registry.py`.

### T+24 to T+48h: Auditability & Persistence
*   Add SQLite/JSON persistence to `SystemState`.
*   Sign `audit.log` entries or implement a remote audit sink.
*   Add basic prompt sanitization for the Agent.

---

## 12. Demo Readiness Assessment

**Verdict: NO-GO.**

The system is currently in a "broken" state for any live demonstration. It will return a 404 when the agent tries to execute an action, and if that is fixed, it will crash with an `AttributeError` on the state manager. Furthermore, the central value proposition (ArmorIQ Governance) is currently a facade.

**Recommendation**: Do not submit until the survival fixes (T+8h) are implemented and verified.
