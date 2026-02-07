#!/bin/bash
set -e

echo "🚀 Starting ArmorIQ Local Demo..."

# 0. Check Ollama
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Ollama is not running. Attempting to start..."
    ollama serve > /dev/null 2>&1 &
    echo "⏳ Waiting for Ollama to initialize..."
    sleep 5
fi

# 1. Start Agent Service (Port 8001)
echo "🤖 Starting Agent Service (Port 8001)..."
uvicorn agent.server:app --host 0.0.0.0 --port 8001 > agent_server.log 2>&1 &
AGENT_PID=$!
echo "   PID: $AGENT_PID"

# 2. Start MCP Simulator (Port 8000)
echo "☁️  Starting MCP Simulator (Port 8000)..."
uvicorn main:app --host 0.0.0.0 --port 8000 > mcp_server.log 2>&1 &
MCP_PID=$!
echo "   PID: $MCP_PID"

# 3. Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 5

# 4. Run Orchestrator Scenario
echo "🎬 Running Orchestrator Scenario..."
# Use MOCK ArmorIQ if no API key provided (optional, but good for demo)
if [ -z "$ARMORIQ_API_KEY" ]; then
    echo "⚠️  No ARMORIQ_API_KEY found. Running in MOCK mode."
    export USE_MOCK_ARMORIQ=true
fi

# Determine python command
PYTHON_CMD="python3"
if [ -f "env/bin/python3" ]; then
    PYTHON_CMD="env/bin/python3"
fi

$PYTHON_CMD -m orchestrator.runner

echo "✅ Demo scenario complete."
echo "   Agent Log: agent_server.log"
echo "   MCP Log: mcp_server.log"
echo ""
echo "🛑 Press Ctrl+C to stop servers..."

# Wait for user input or just exit?
# Usually run_demo keeps servers alive or orchestrator runs once and exits?
# The orchestrator runs one cycle and exits.
# But we spawned background processes. We should trap exit to kill them.

trap "kill $AGENT_PID $MCP_PID; exit" INT TERM
wait
