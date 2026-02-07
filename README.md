# ArmorIQ Autonomous Sysadmin Agent

**Team Name**: Autonomous Guardians
**Project Status**: Hackathon Submission (Stabilized & Governed)

## 1. Project Overview

Autonomous AI agents often face a "trust gap": they are either too restricted to be useful or too powerful to be safe. This project bridge that gap by implementing a **Governed Sysadmin Assistant**.

Our system manages infrastructure autonomously (detecting failures, restarting services, resolving alerts) but operates under a strict **Policy-in-the-Loop** model. Unlike typical agents that call APIs directly, our agent must first articulate its **Intent** to the **ArmorIQ Governance Engine**. Only when ArmorIQ issues a cryptographically signed **Intent Token** can the system (MCP) execute the requested action.

**Key Differentiators:**
- **Separation of Reasoning and Execution**: The agent reasons freely but has ZERO direct authority.
- **Cryptographic Action Binding**: Intent tokens are bound to specific tools and parameters (e.g., "Restart only service X").
- **Audit-First Design**: Every attempted, approved, and executed action is cryptographically linked and logged.

---

## 2. System Architecture

```text
    [ Human / Trigger ]
           |
           v
    +-------------------+      +-----------------------+
    |   Agent (Ollama)  |----->| ArmorIQ Governance    |
    |   (Reasoning)     |      | (Policy Enforcement)  |
    +-------------------+      +-----------+-----------+
           ^                               |
           | Sensing                       | Intent Token (JWT)
           |                               v
    +------+------------+      +-----------------------+
    |   System (MCP)    |<-----| Orchestrator Runner   |
    |   (Execution)     |      | (Coordination)        |
    +-------------------+      +-----------------------+
           |                               ^
           v                               |
    +-------------------+                  |
    | React Dashboard   |<-----------------+
    | (Visualization)   |
    +-------------------+
```

- **Agent**: A local FastAPI service wrapping Ollama (`llama3.2`) to generate remediation plans.
- **Orchestrator**: The "hands" of the system. It fetches system state, requests plans, secures governance tokens, and invokes the MCP.
- **ArmorIQ Gateway**: The authority that validates plans against policies and issues signed JWT Intent Tokens.
- **MCP (Mini Cloud Platform)**: A high-fidelity server simulator that acts as the **Policy Enforcement Point (PEP)**. It rejects any command without a valid, bound token.
- **Frontend**: A modern React/Vite dashboard for real-time monitoring of system health and agent logic.

---

## 3. Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **Ollama**: Installed and running locally (`ollama pull llama3.2`)
- **Git**: To clone the repository

---

## 4. Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/armoriq-sysadmin-agent.git
cd armoriq-sysadmin-agent
```

### 2. Backend Setup
```bash
# It is recommended to use a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

---

## 5. Configuration

Create a `.env` file in the `backend/` directory:

```bash
# backend/.env

# ArmorIQ Configuration (Optional for Demo)
# ARMORIQ_API_KEY="your-real-key"
# ARMORIQ_USER_ID="your-user-id"
# ARMORIQ_AGENT_ID="your-agent-id"

# Security Configuration (Used for Demo Governance)
ARMORIQ_SECRET="demo-secret-key-12345"
USE_MOCK_ARMORIQ=true

# Agent Configuration
OLLAMA_MODEL="llama3.2"
AGENT_API_KEY="default-insecure-key"
```

---

## 6. Running the System

### Step 1: Start the Backend Services
The demo script launches the Agent Service, the MCP Simulator, and runs a management cycle.
```bash
# From the root directory
./backend/scripts/run_demo.sh
```

### Step 2: Start the Frontend Dashboard
In a new terminal:
```bash
cd frontend
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 7. Demo Walkthrough

### Scenario A: Normal Autonomous Recovery
1. Run `python3 backend/insert_issues.py alert` to inject a failure.
2. The Orchestrator (via `run_demo.sh`) will:
   - Detect the critical alert.
   - Request a plan from the Agent.
   - Secure a signed token from ArmorIQ.
   - Execute the fix on MCP.
3. Observe the `audit.log` for the successful execution.

### Scenario B: Security Boundary Verification
To prove the system is secure, run our governance test suite:
```bash
python3 backend/scripts/test_governance.py
```
This script verifies:
- ✓ **Valid tokens** are accepted.
- ✗ **Badly signed tokens** are blocked.
- ✗ **Out-of-scope actions** (e.g., trying to restart service B with a token for service A) are blocked.
- ✗ **Token Reuse** (replay attacks) is blocked.

---

## 8. Security & Governance Model

Our implementation follows the **ArmorIQ MCP Specification**:

- **Intent Tokens**: Every mutating action requires a JWT in the `intent_token` field.
- **Action Binding**: The token contains an `actions` claim. The MCP verifies that the `tool_name` and `parameters` in the request match exactly what was authorized in the token.
- **Scope Enforcement**: Tokens are short-lived (10 mins) and unique per action attempt.
- **JTI-based Blacklisting**: The MCP tracks Token IDs (`jti`) to prevent the same token from being used twice.

---

## 9. Project Structure

- `backend/agent/`: LLM integration and plan generation logic.
- `backend/mcp/`: The core system simulator and policy enforcement logic.
- `backend/orchestrator/`: The loop that drives the autonomous behavior.
- `backend/armoriq/`: Client wrapper for governance token issuance.
- `backend/system/`: Core state management and audit logging.
- `frontend/`: React/Tailwind source for the dashboard.

---

## 10. Known Limitations

- **Mock Governance**: For demo purposes, we use HS256 with a shared secret. Production ArmorIQ uses RS256/Asymmetric keys.
- **In-Memory State**: The MCP simulator resets its state on restart.
- **Local LLM**: Performance is dependent on your local Ollama speed. Llama3.2 is recommended for the best balance.

---

## 11. Troubleshooting

- **404 on Execute**: Ensure `run_demo.sh` is running; it starts the server at `mcp.main:app`.
- **AttributeError: 'SystemState' object has no attribute 'get_alert'**: Ensure you are using the stabilized version of the code (this was a known bug fixed in the audit phase).
- **Ollama Connection Refused**: Ensure `ollama serve` is running in the background.

---

## 12. License & Attribution

This project is submitted for the **ArmorIQ Hackathon 2024**.

**Authors**: Harshit Singh Bhandari & Team.
**Lead Engineer for Audit/Fixes**: Jules.

*Built with ArmorIQ, FastAPI, and React.*
