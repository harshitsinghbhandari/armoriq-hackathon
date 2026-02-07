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
*   Running Keycloak instance (configured with realm `hackathon`)
*   Gemini API Key

### Setup
1.  Clone the repository.
2.  Install dependencies: `pip install -r requirements.txt` (or manually install `google-genai`, `python-dotenv`, `requests`, `uvicorn`, `fastapi`).
3.  Set up environment variables in `.env`:
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

## Tech Stack
*   **AI:** Google Gemini 2.5 Flash
*   **Backend:** FastAPI / Python
*   **Auth:** Keycloak (OpenID Connect)
*   **Protocol:** Model Context Protocol (MCP) concepts
*   **Governance:** Custom Policy Engine

## Team
*   [Participant Name] - [Role]
*   [Participant Name] - [Role]
