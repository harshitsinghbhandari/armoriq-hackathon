# ArmorIQ Governance Integration Plan

**Goal:** Ensure 100% compliant, governed autonomous sysadmin agent for hackathon submission.

## 🔴 Must Do (Before Submission)

*   [ ] **Register MCPs in ArmorIQ**
    *   Define the "MCP" resource in the ArmorIQ dashboard.
    *   configure allowed actions (e.g., `infra.restart`, `alert.resolve`).
*   [ ] **Validate Plan Schemas**
    *   Ensure the JSON schema sent to `capture_plan` matches exactly what ArmorIQ expects.
    *   Test with `agent_id`, `user_id`, and `action` fields.
*   [ ] **Enforce Token-Only Execution**
    *   Audit `mcp/` endpoints. **EVERY** mutating endpoint must depend on `verify_armoriq`.
    *   **Verify:** sending a request without a token returns `401 Unauthorized`.
    *   **Verify:** sending a request with a fake token returns `403 Forbidden`.
*   [ ] **Complete Agent Registry Setup**
    *   Ensure the Agent's identity (`agent_id`) is properly registered and has the `operator` role in ArmorIQ.
*   [ ] **Remove Direct MCP Access**
    *   Grep codebase for any `requests.post` to `mcp/` that *doesn't* use the ArmorIQ client.
    *   Delete/Refactor `agent_basic.py` legacy code if it still exists.

## 🟠 Should Do (If Time Allows)

*   [ ] **Delegation Scenario**
    *   Create a policy that *denies* a specific high-risk action (e.g., `infra.delete`).
    *   Effect: Agent receives denial, and the fallback logic should log "Escalating to Human".
*   [ ] **Multi-Agent Testing**
    *   Spin up two agent processes.
    *   Verify they don't race-condition on the same alert (needs locking or simple ownership check).
*   [ ] **Policy Tuning**
    *   Refine rate limits (e.g., "Max 5 failures per hour").
*   [ ] **Audit Export**
    *   Script to dump the `audit.log` to a clean CSV for judges to review.

## 🟢 Nice to Have

*   [ ] **UI Dashboard**
    *   Simple web view of `mcp/list` and `audit.log`.
*   [ ] **Visualization**
    *   Sequence diagram generator from the log file.
*   [ ] **Load Testing**
    *   Run `insert_issues.py storm 50` and ensure the governance gateway doesn't choke.

## 📖 Mandatory Reading

1.  [docs.armoriq.ai](https://docs.armoriq.ai) - **READ THE API REFERENCE**
2.  `README.md` - System architecture & setup.
3.  `DOCUMENTATION.md` - Internal mechanics & failure modes.

## ⚠️ Rules

1.  **NO Bypassing ArmorIQ**: Violating this disqualifies the entry.
2.  **NO Hardcoded Tokens**: All intent tokens must be dynamically fetched.
3.  **NO Direct MCP Calls**: The agent must **NEVER** speak to the MCP directly for actions. Only for "sensing" (read-only).

## 👥 Ownership

| Role | Assignee | Responsibilities |
| :--- | :--- | :--- |
| **Agent / LLM** | *TBD* | Plan generation, Prompt engineering, Ollama setup. |
| **Governance** | *TBD* | ArmorIQ dashboard config, Policy definitions, SDK integration. |
| **System (MCP)** | *TBD* | Endpoint protection, Token verification logic, Database/State. |
| **Orchestrator** | *TBD* | The glue code, error handling, retries. |
