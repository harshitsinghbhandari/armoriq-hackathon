# ArmorIQ Hackathon Submission: Autonomous Sysadmin Agent

## 🚀 Project Overview

This project implements an **Autonomous Sysadmin Assistant** that leverages **Ollama** (local LLM) to reason about system health and **ArmorIQ** to govern and authorize execute actions. The system is designed to autonomously detect issues (e.g., stopped services, high CPU usage), propose remediation plans, and execute them safely under strict policy control.

Unlike typical improved CLI tools, this agent introduces a **Governance Layer** where every action is:
1.  **Planned**: The agent reasons about the state and proposes a plan.
2.  ** governed**: The plan is submitted to ArmorIQ for policy checks and approval.
3.  **Token-Gated**: Execution on the system (MCP) is only possible with a valid, signed **Intent Token** from ArmorIQ.
4.  **Verified**: The system guarantees that the executed action matches the approved intent.

## 🏗️ Architecture

The system follows a strict **Plan -> Govern -> Execute** loop.

```mermaid
graph TD
    subgraph "Local Environment"
        System[Managed System (MCP)]
        Agent[Ollama Agent]
        Orchestrator[Orchestrator Loop]
    end
    
    subgraph "Cloud / Governance"
        ArmorIQ[ArmorIQ Policy Engine]
    end

    System -- 1. State (Services, Alerts) --> Orchestrator
    Orchestrator -- 2. State --> Agent
    Agent -- 3. Proposed Plan (JSON) --> Orchestrator
    
    Orchestrator -- 4. Submit Plan --> ArmorIQ
    ArmorIQ -- 5. Approve & Sign --> Orchestrator
    
    Orchestrator -- 6. Execute (Action + Intent Token) --> System
    System -- 7. Validate Token & Action --> Orchestrator
```

### Components
-   **Agent (Ollama)**: A local LLM service that receives system state and outputs a structured remediation plan.
-   **ArmorIQ**: The governance authority. It reviews plans against policies and issues cryptographic Intent Tokens for approved actions.
-   **System (MCP)**: A "Mini Cloud Platform" simulator that mimics a real server environment. It allows actions (like `restart_service`) ONLY IF accompanied by a valid ArmorIQ Intent Token.
-   **Orchestrator**: A lightweight runner that coordinates the cycle between these components.

## 🛡️ Key Guarantees

1.  **Plan-Based Execution**: The agent never acts impulsively. It must first articulate a plan, which is reviewed before any side-effect occurs.
2.  **Token-Gated Actions**: The `mcp` (System) endpoints are locked. They require an `x-armoriq-intent-token` header. This token is *only* obtainable via the ArmorIQ approval flow.
3.  **No Undeclared Actions**: The Intent Token binds a specific action and parameters to the approval. The agent cannot get approval for "check status" and then execute "delete database".

## 🛠️ Prerequisites

-   **Python 3.10+**
-   **Ollama**: Running locally with a capable model (e.g., `llama3` or `mistral`).
    -   `ollama pull mistake` (or your preferred model)
-   **ArmorIQ API Key**: Sign up at [ArmorIQ](https://armoriq.com) (or use Mock mode).
-   **Java (Optional)**: For running a local Keycloak instance if standard authentication is required.

## ⚡ Quickstart

### 1. Installation

```bash
git clone https://github.com/your-repo/armoriq-agent.git
cd armoriq-agent
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file or export the necessary variables:

```bash
# ArmorIQ Configuration
export ARMORIQ_API_KEY="your-api-key-here"

# (Optional) If using a specific local model
export OLLAMA_MODEL="mistral"
```

*Note: If `ARMORIQ_API_KEY` is missing, the system will run in **MOCK** mode for demonstration purposes.*

### 3. Run the Demo

We provide a script that spins up the Agent, the MCP System, and runs the Orchestrator loop.

```bash
./scripts/run_demo.sh
```

## 🎥 Demo Walkthrough

When you run the demo, the following happens:

1.  **Boot**: The Agent Service (port 8001) and MCP Simulator (port 8000) start up.
2.  **Sense**: The Orchestrator queries the MCP for current status.
    -   *Example: "Service 'web-server' is CRITICAL (stopped)."*
3.  **Plan**: The Agent analyzes the state and proposes a fix.
    -   *Plan: "Restart 'web-server' to restore availability."*
4.  **Govern**: The plan is sent to ArmorIQ. Use the ArmorIQ dashboard to see the request (if using the real API).
    -   *Status: Approved. Token Issued.*
5.  **Act**: The Orchestrator calls the `restart_service` endpoint on the MCP with the Intent Token.
6.  **Verify**: The service restarts, and the new state is reflected in the next cycle.

## 📂 Repository Structure

```text
├── agent/            # Ollama-based Agent Service (FastAPI)
├── armoriq/          # ArmorIQ Client & SDK Integration
├── auth/             # Keycloak Authentication Helpers
├── mcp/              # Mini Cloud Platform (System Simulator)
├── orchestrator/     # Main control loop (Runner)
├── policy/           # Policy definitions (if local)
├── scripts/          # Startup and utility scripts
├── .env.example      # Environment variable template
└── requirements.txt  # Python dependencies
```

## ⚠️ Limitations

-   **Mock Mode**: Without a valid ArmorIQ API Key, the system mimics governance approval locally.
-   **Local Only**: Currently configured for `localhost` execution.
-   **Single Cycle**: The demo script runs a limited number of cycles to demonstrate the flow.

## 👥 Team & Credits

**Team Name**: [Your Team Name]

-   **Harshit Singh Bhandari** - Agent & Orchestrator
-   [Teammate Name] - ArmorIQ Integration
-   [Teammate Name] - MCP Simulator

Built for the **ArmorIQ Hackathon 2024**.
