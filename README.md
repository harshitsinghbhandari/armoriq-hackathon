# ArmorIQ Autonomous Sysadmin Agent

Autonomous infrastructure management with cryptographically enforced governance.

## Quickstart

1. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Run the Demo**:
   ```bash
   ./backend/scripts/run_demo.sh
   ```

3. **Verify Governance**:
   ```bash
   python3 backend/scripts/test_governance.py
   ```

## Architecture
- **Agent**: Reasons about system state and proposes JSON plans.
- **ArmorIQ**: Reviews plans and issues signed **Intent Tokens** (JWT).
- **MCP**: Executes actions ONLY if the token is valid and bound to the specific action/params.

## Key Security Features
- **JWT Verification**: Cryptographic signature checks on all mutating actions.
- **Action Binding**: Tokens are locked to specific tools and parameters.
- **Reuse Prevention**: JTI-based tracking prevents token replay attacks.
- **Identity Binding**: Ensures the executing user matches the token subject.
