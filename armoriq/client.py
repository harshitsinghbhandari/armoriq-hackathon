import os
import json
import logging
import dotenv
import requests
from typing import Dict, Any

dotenv.load_dotenv()

# Logger
logger = logging.getLogger("armoriq")

class ArmorIQGateway:
    def __init__(self):
        self.use_mock = os.getenv("USE_MOCK_ARMORIQ", "false").lower() == "true"
        self.client = None
        
        if not self.use_mock:
            self._init_real_client()
        else:
            logger.info("⚠️ ArmorIQ Gateway running in MOCK mode.")

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

    def capture_plan(self, llm: str, prompt: str, plan: Dict[str, Any]) -> str:
        """
        Captures the generated plan with ArmorIQ.
        Returns a plan reference ID (or the plan object itself, depending on SDK).
        """
        if self.use_mock:
            logger.info(f"[MOCK] Capturing plan from {llm}")
            return "mock-plan-id-123"
        
        return self.client.capture_plan(
            llm=llm,
            prompt=prompt,
            plan=plan
        )

    def get_intent_token(self, captured_plan: Any) -> str:
        """
        Obtains an intent token for the captured plan.
        """
        if self.use_mock:
            logger.info("[MOCK] Requesting intent token...")
            return "mock-intent-token-xyz"

        return self.client.get_intent_token(captured_plan)

    def invoke(self, mcp: str, action: str, intent_token: str, params: Dict[str, Any], user_email: str) -> Dict[str, Any]:
        """
        Invokes an action via the ArmorIQ gateway.
        """
        if self.use_mock:
            logger.info(f"[MOCK] Invoking {action} on {mcp} with token {intent_token[:5]}...")
            
            # Map action to endpoint
            endpoint = ""
            if action == "infra.restart":
                endpoint = "/mcp/infra/restart"
            elif action == "alert.resolve":
                endpoint = "/mcp/alerts/resolve"
            else:
                logger.warning(f"[MOCK] Unknown action {action}, failing execution.")
                raise ValueError(f"Unknown action: {action}")

            url = f"{mcp}{endpoint}"
            headers = {
                "X-ArmorIQ-Intent-ID": intent_token,
                "X-ArmorIQ-User-Email": user_email,
                "Content-Type": "application/json"
            }
            
            try:
                resp = requests.post(url, json=params, headers=headers, timeout=5)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"[MOCK] Execution failed: {e}")
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
