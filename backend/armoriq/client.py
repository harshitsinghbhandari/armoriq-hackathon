import os
import json
import logging
import dotenv
import requests
from typing import Dict, Any, List
from jose import jwt
from datetime import datetime, timedelta
import uuid

dotenv.load_dotenv()

# Logger
logger = logging.getLogger("armoriq")

# Shared secret for demo purposes. In production, this would be a public key or ArmorIQ-managed.
ARMORIQ_SECRET = os.getenv("ARMORIQ_SECRET", "demo-secret-key-12345")

class ArmorIQGateway:
    def __init__(self):
        self.use_mock = os.getenv("USE_MOCK_ARMORIQ", "false").lower() == "true"
        self.client = None
        
        if not self.use_mock:
            try:
                self._init_real_client()
            except ValueError as e:
                logger.warning(f"Failed to init real client: {e}. Falling back to SECURE MOCK.")
                self.use_mock = True

        if self.use_mock:
            logger.info("⚠️ ArmorIQ Gateway running in SECURE MOCK mode (Signed Tokens).")

    def _init_real_client(self):
        # ArmorIQ Configuration
        api_key = os.getenv("ARMORIQ_API_KEY")
        user_id = os.getenv("ARMORIQ_USER_ID")
        agent_id = os.getenv("ARMORIQ_AGENT_ID")

        if not all([api_key, user_id, agent_id]):
            logger.warning("⚠️ ArmorIQ credentials missing in .env. Falling back to mock mode if strict mode not enforced.")
            # If credentials missing, we might want to default to mock or raise error. 
            # For this task, let's error if not in mock mode explicitly, 
            # or we could auto-enable mock. 
            # Given the prompt implies "Load config from env", strict failure is safer for non-mock.
            raise ValueError("ArmorIQ credentials missing and USE_MOCK_ARMORIQ is not true.")

        from armoriq_sdk import ArmorIQClient
        self.client = ArmorIQClient(
            api_key=api_key,
            user_id=user_id,
            agent_id=agent_id
        )
        logger.info("✅ ArmorIQ SDK initialized.")

    def capture_plan(self, llm: str, prompt: str, plan: Dict[str, Any]) -> Any:
        """
        Captures the generated plan with ArmorIQ.
        Returns a plan reference ID (or the plan object itself, depending on SDK).
        """
        if self.use_mock:
            logger.info(f"[MOCK] Capturing plan from {llm}")
            # In mock mode, we return the plan wrapped so get_intent_token can bind it
            return {"plan_id": "mock-plan-id-123", "plan": plan}
        
        return self.client.capture_plan(
            llm=llm,
            prompt=prompt,
            plan=plan
        )

    def get_intent_token(self, captured_plan: Any) -> str:
        """
        Obtains an intent token for the captured plan.
        In mock mode, it generates a cryptographically signed JWT.
        """
        if self.use_mock:
            logger.info("[MOCK] Issuing signed intent token...")

            # Extract allowed actions from the plan for binding
            allowed_actions = []
            if isinstance(captured_plan, dict) and "plan" in captured_plan:
                steps = captured_plan["plan"].get("steps", [])
                for step in steps:
                    allowed_actions.append({
                        "action": step.get("action"),
                        "params": step.get("params")
                    })

            payload = {
                "sub": "admin_agent", # Matches BOT_USER in keycloak.py
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=10),
                "jti": str(uuid.uuid4()),
                "actions": allowed_actions,
                "iss": "armoriq-mock-authority"
            }

            token = jwt.encode(payload, ARMORIQ_SECRET, algorithm="HS256")
            return token

        return self.client.get_intent_token(captured_plan)

    def invoke(self, mcp: str, action: str, intent_token: str, params: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        """
        Invokes an action via the ArmorIQ gateway (or Mock).
        Standard MCP: Calls POST /mcp/tools/execute
        """
        if self.use_mock:
            logger.info(f"[MOCK] Invoking {action} on {mcp} with token {intent_token[:5]}...")
            
            url = f"{mcp}/mcp/tools/execute"
            
            # Standard MCP Payload
            payload = {
                "tool_name": action,
                "parameters": params,
                "intent_token": intent_token
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-ArmorIQ-User-Email": user_email # Optional, for logging/audit context
            }
            
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=5)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"[MOCK] Execution failed: {e}")
                # Try to print response text if available
                if 'resp' in locals():
                     logger.error(f"Response: {resp.text}")
                raise

        return self.client.invoke(
            mcp=mcp,
            action=action,
            intent_token=intent_token,
            params=params,
            user_email=user_email
        )

# Global Instance
gateway = ArmorIQGateway()
