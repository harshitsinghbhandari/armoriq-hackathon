# TODO List

> **READ README.md, DOCUMENTATION.md, AND ARMORIQ DOCS BEFORE CODING**

## Short-Term Tasks
- [ ] **ArmorIQ SDK Integration:** Replace `policy/engine.py` logic with the official SDK. <!-- @owner: TBD -->
- [ ] **Demo Recording:** Create a walkthrough video demonstrating the agent resolving a "storm" scenario. <!-- @owner: TBD -->
- [ ] **Policy Hardening:** Implement checks for "ownership" (agent can only resolve alerts they are assigned). <!-- @owner: TBD -->
- [ ] **Delegation Scenario:** Add a scenario where the agent encounters an unknown error and escalates to a human operator. <!-- @owner: TBD -->
- [ ] **Edge-Case Testing:** Test with malformed JSON, network timeouts, and invalid auth tokens. <!-- @owner: TBD -->

## Medium-Term Tasks
- [ ] **Persistent Storage:** Replace in-memory lists in `mcp/` with a database (SQLite/PostgreSQL).
- [ ] **Dashboard UI:** Build a simple frontend to visualize the state and audit log.
- [ ] **Multi-Agent Support:** Allow multiple agents to cooperate on resolving complex incidents.

## Nice-To-Have Tasks
- [ ] **LLM Fine-Tuning:** Fine-tune a smaller model specifically for this sysadmin vocabulary.
- [ ] **CI/CD Pipeline:** Automate testing and deployment of the governance policy.

## Execution Guide
*   **Pick a task:** Assign yourself by replacing `TBD` with your name.
*   **Create a branch:** `feat/short-description`.
*   **Implement & Test:** Verify locally using `insert_issues.py`.
*   **PR & Review:** Request review from at least one peer.
