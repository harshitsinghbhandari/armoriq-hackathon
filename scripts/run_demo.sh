#!/bin/bash

# Kill ports 8000 and 8001
echo "Cleaning up ports..."
lsof -ti :8000 | xargs kill -9 2>/dev/null
lsof -ti :8001 | xargs kill -9 2>/dev/null

# Start MCP
echo "Starting MCP Simulator on port 8000..."
cd backend
/env/bin/python -m uvicorn mcp.main:app --host 0.0.0.0 --port 8000 --reload &
MCP_PID=$!
cd ..

# Start Agent
echo "Starting Agent Service on port 8001..."
cd backend
/env/bin/python -m uvicorn agent.server:app --host 0.0.0.0 --port 8001 --reload &
AGENT_PID=$!
cd ..

echo "Services started."
echo "MCP PID: $MCP_PID"
echo "Agent PID: $AGENT_PID"
echo "Press Ctrl+C to stop."

wait
