# ArmorIQ Agent Frontend

A minimal React dashboard for controlling and monitoring the ArmorIQ agent.

## Setup

1.  **Install Dependencies:**
    ```bash
    cd frontend
    npm install
    ```

2.  **Start Development Server:**
    ```bash
    npm run dev
    ```
    Typically runs on `http://localhost:5173`.

## Architecture

This frontend is a **pure client** that proxies API requests to the Python backend services:

*   **Frontend**: React + Vite + Tailwind CSS
*   **Backend Proxies**:
    *   `/api/run` -> `http://localhost:8001/run` (Agent Service)
    *   `/api/mcp` -> `http://localhost:8000/mcp` (MCP Service)

## Key Components

*   **Control Panel**: Trigger agent cycles.
*   **System State**: View live infrastructure and alerts.
*   **Agent Plan**: Inspect the agent's decision-making logic.
*   **Log Viewer**: (Optional) View system logs.

## Troubleshooting

*   **CORS Errors**: If you see network errors, ensure `vite.config.js` proxy settings match your running backend ports.
*   **Backend Not Running**: Ensure `scripts/run_demo.sh` is running in another terminal.
