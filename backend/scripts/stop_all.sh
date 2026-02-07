#!/bin/bash

echo "🛑 Stopping all demo services..."

pkill -f "uvicorn agent.server:app --host 0.0.0.0 --port 8001"
echo "   Killed Agent (Port 8001)"

pkill -f "uvicorn.*--port 8000"
echo "   Killed MCP (Port 8000)"

ollama stop > /dev/null 2>&1
echo "   Stopped Ollama (if running via serve)"

echo "✅ All demo services stopped."
