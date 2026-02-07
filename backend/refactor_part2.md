# Refactor insert_issues.py

## `reset_system` function
- Update `requests.post` calls to `infra.restart` and `alerts.resolve` to use `/mcp/tools/execute`.
- Payload: `{"tool_name": "...", "parameters": {...}, "intent_token": "sim-reset-token"}`.

# Verify prompts.py
- Ensure tool definitions in system prompt match `registry.py`.
