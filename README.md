# ArmorIQ Autonomous Sysadmin Agent

## 🚀 1. Project Overview

### The Problem
Modern cloud infrastructure is complex and moves faster than human operators can monitor. AI Agents are promising for autonomous management, but they lack **governance**. An agent with "root" access can accidentally (or maliciously) cause catastrophic outages if it hallucinates a command or is misdirected.

### The Solution: ArmorIQ Governance
This project implements an **Autonomous Sysadmin Assistant** that detects system issues and proposes remediation plans. Unlike standard agents, it is governed by **ArmorIQ**.

**Governance is central because:**
- **Policy-in-the-Loop**: Every action must be approved by a policy engine before execution.
- **Cryptographic Intent**: The infrastructure (MCP) only executes actions accompanied by a signed **Intent Token** from ArmorIQ.
- **Strict Binding**: Tokens are bound to specific actions and parameters (e.g., "Restart Web Server" != "Delete Database").

### What Makes This Different
Traditional agents are "trusted" once authenticated. This system operates on **Zero Trust** for the agent. The agent is the "intelligence," ArmorIQ is the "authority," and the MCP is the "enforcer."

---

## 🏗️ 2. System Architecture

The system follows a strict **Sense -> Plan -> Govern -> Act** loop.

```text
+----------------+       +-------------------+       +----------------------+
|   Frontend     | <---> |  Agent Service    | <---> |  Ollama (Local LLM)  |
| (React Dashboard)|     | (FastAPI, :8001)  |       +----------------------+
+----------------+       +---------+---------+
                                   |
                                   v
                         +---------+---------+       +----------------------+
                         |   Orchestrator    | <---> |  ArmorIQ (Governance)|
                         | (Control Loop)    |       | (Policy & Tokens)    |
                         +---------+---------+       +----------------------+
                                   |
                                   v
                         +---------+---------+
                         |   MCP Simulator   |
                         | (FastAPI, :8000)  |
                         +-------------------+
```

- **Agent Service**: Uses Ollama to analyze system state and propose a remediation plan in JSON.
- **Orchestrator**: Coordinates the flow between the Agent, ArmorIQ, and the MCP. (Integrated into the Agent Service for the web demo).
- **ArmorIQ**: Reviews the plan against security policies. If approved, it issues a signed **Intent Token**.
- **MCP (Mini Cloud Platform)**: A simulator representing your infrastructure. It enforces that every mutating action has a valid ArmorIQ token.
- **Frontend**: A React-based dashboard to visualize system health, agent reasoning, and governance status.

---

## 🛠️ 3. Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher (for Frontend)
- **Ollama**: Running locally ([Download here](https://ollama.com/))
  - Recommended model: `llama3.2` or `mistral`
- **ArmorIQ Account**: (Optional) For real policy enforcement. Otherwise, use **Mock Mode**.

---

## 📥 4. Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/armoriq-agent.git
cd armoriq-agent
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

---

## ⚙️ 5. Configuration

Create a `.env` file in the `backend/` directory:

```bash
# ArmorIQ Configuration
# Set to 'true' to run without a real ArmorIQ API Key
USE_MOCK_ARMORIQ=true

# Secret for Mock Token signing (Must match between Agent and MCP)
ARMORIQ_SECRET=demo-secret-key-12345

# Agent API Key (for Frontend communication)
AGENT_API_KEY=default-insecure-key

# Mock LLM (Set to 'true' to bypass Ollama for testing)
MOCK_LLM=true

# Ollama Configuration
OLLAMA_MODEL=llama3.2
```

---

## 🏃 6. Running the System

### Step 1: Start Ollama
Ensure Ollama is running and you have pulled the model:
```bash
ollama run llama3.2
```

### Step 2: Start Backend Services
Use the provided script to start the MCP and Agent services:
```bash
./scripts/run_demo.sh
```
- **MCP Simulator**: [http://localhost:8000](http://localhost:8000)
- **Agent Service**: [http://localhost:8001](http://localhost:8001)

### Step 3: Start Frontend
In a new terminal:
```bash
cd frontend
npm run dev
```
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)

---

## 🎥 7. Demo Walkthrough

### Scenario: Healing a Critical Service

1. **View Clean State**: Open the dashboard at `http://localhost:5173`. You should see all services as "Healthy".
2. **Inject a Fault**: Simulate a service failure by creating a critical alert.
   ```bash
   curl -X POST http://localhost:8000/mcp/alerts/create \
     -H "Content-Type: application/json" \
     -d '{"type": "service", "msg": "Service payments is DOWN", "severity": "critical", "resource_id": "payments"}'
   ```
3. **Trigger Agent**: Click **"Run Agent"** in the UI (or use the command below).
   ```bash
   curl -X POST http://localhost:8001/run \
     -H "X-API-Key: default-insecure-key" \
     -H "Content-Type: application/json" \
     -d '{"input": "Restore system health"}'
   ```
4. **Observe Governance**:
   - The Agent analyzes the alert.
   - It proposes `infra.restart(service_id="payments")`.
   - The Orchestrator sends the plan to ArmorIQ.
   - ArmorIQ approves and issues a token.
   - The MCP executes the restart only because the token is valid.
5. **Blocked Action**: Try to scale a service without an approved plan (Direct MCP call).
   ```bash
   curl -X POST http://localhost:8000/mcp/tools/execute \
     -H "Content-Type: application/json" \
     -d '{"tool_name": "infra.scale", "parameters": {"service_id": "auth", "replicas": 10}, "intent_token": "invalid-token"}'
   ```
   *Expect: 403 Forbidden.*
6. **Verify Audit Log**: Check the security logs to see the authorized actions.
   - Available in the dashboard or via the MCP `security.audit_log` tool.

---

## 🛡️ 8. Security & Governance Model

- **Intent Tokens**: JWTs signed by ArmorIQ that prove a specific action was reviewed and authorized.
- **Action Binding**: The token contains the specific `tool_name` and `parameters` allowed. MCP rejects any mismatch.
- **Scope Enforcement**: The agent can only see and act on resources within its defined scope (e.g., `infra`, `alerts`).
- **Role Enforcement**: ArmorIQ validates the user/agent identity (via Keycloak or Mock Sub) before issuing tokens.

---

## 📂 9. Project Structure

```text
├── backend/
│   ├── agent/         # Ollama Agent logic & FastAPI server
│   ├── armoriq/       # Integration with ArmorIQ SDK / Mock
│   ├── mcp/           # Mini Cloud Platform (The Enforcement Point)
│   ├── orchestrator/  # Background control loop logic
│   ├── system/        # Core state management & logging
│   └── data/          # Persistent state (JSON files)
├── frontend/          # React + Vite + Tailwind Dashboard
├── scripts/           # Demo automation scripts
└── README.md          # You are here
```

---

## ⚠️ 10. Known Limitations

- **Mock Mode**: While Mock mode signs tokens, it uses a shared secret for simplicity. Production requires asymmetric keys.
- **Local Ollama**: Performance depends on your local hardware. If slow, consider smaller models like `phi3`.
- **Stateless Agent**: The agent does not currently maintain long-term memory between cycles; it relies on the current system state.

---

## 🔧 11. Troubleshooting

- **Ollama Connection Refused**: Ensure Ollama is running (`ollama serve`).
- **401 Unauthorized**: Ensure `X-API-Key` matches `AGENT_API_KEY` in `.env`.
- **403 Forbidden on MCP**: Ensure `ARMORIQ_SECRET` is identical in all components.
- **Frontend Proxy Error**: Check `vite.config.js` and ensure backend ports (8000/8001) are correct.

---

## 📜 12. License & Attribution

Built for the **ArmorIQ Hackathon 2024**.

**Team:**
- **Harshit Singh Bhandari** - Lead Engineer
- [Your Name/Teammate] - Governance & Security
- [Your Name/Teammate] - Frontend & UX

Licensed under the MIT License.
