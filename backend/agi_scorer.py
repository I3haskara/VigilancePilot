
import httpx
import json
import os
from typing import Dict, List, Any
import logging
import asyncio

async def _call_agi_api(message_text: str) -> Dict[str, Any]:
    """
    Async AGI session API call using httpx
    """
    AGI_BASE_URL = os.getenv("AGI_BASE_URL", "https://api.agi.tech/v1")
    AGI_API_KEY = os.getenv("AGI_API_KEY")
    if not AGI_API_KEY:
        raise AgiUnavailable("AGI_API_KEY is not set")
    headers = {
        "Authorization": f"Bearer {AGI_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # 1) Create session
            create_resp = await client.post(
                f"{AGI_BASE_URL}/sessions",
                headers=headers,
                json={"name": "vigilancepilot-session"}
            )
            create_resp.raise_for_status()
            session_id = create_resp.json()["id"]
            # 2) Send message
            send_resp = await client.post(
                f"{AGI_BASE_URL}/sessions/{session_id}/message",
                headers=headers,
                json={"message": message_text}
            )
            send_resp.raise_for_status()
            # 3) Fetch messages
            msgs_resp = await client.get(
                f"{AGI_BASE_URL}/sessions/{session_id}/messages",
                headers=headers,
                params={"after_id": 0}
            )
            msgs_resp.raise_for_status()
            data = msgs_resp.json()
            messages: List[Dict[str, Any]] = data.get("messages") or data.get("data") or []
            if not messages:
                raise AgiUnavailable("No messages returned from AGI")
            assistant_msg = next(
                (m for m in reversed(messages) if m.get("role") == "assistant"),
                messages[-1],
            )
            content = assistant_msg.get("content") or assistant_msg.get("message") or ""
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = {
                    "risk_level": "unknown",
                    "risk_score": 0,
                    "categories_detected": [],
                    "ai_reasoning": content,
                }
            return {
                "risk_level": parsed.get("risk_level", "unknown"),
                "risk_score": parsed.get("risk_score", 0),
                "categories_detected": parsed.get("categories_detected", []),
                "ai_reasoning": parsed.get("ai_reasoning", content),
            }
    except Exception as e:
        logger.exception("AGI request failed")
        raise AgiUnavailable(str(e)) from e
"""
AGI Browser Agent Integration (Session-Based API)
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import asyncio
import httpx
from dotenv import load_dotenv

from .rule_engine import RuleEngine
from .risk_aggregator import aggregate_risk, classify_risk_level

from .models import (
    MessageAnalysisRequest,
    MessageAnalysisResponse,
    BatchAnalysisRequest,
    AlertConfig,
    HealthCheck,
    WebhookEvent,
    TelnyxCallRequest,
    ScoreResponse,
    RiskLevel,
)

load_dotenv()
logger = logging.getLogger(__name__)


class AgiUnavailable(Exception):
    """Exception raised when AGI API is unavailable or returns an error"""
    pass


class AGIScorer:
    def __init__(self):
        """Initialize AGI Scorer"""
        api_key = os.getenv("AGI_API_KEY")
        base_url = os.getenv("AGI_BASE_URL", "https://api.agi.tech/v1")
        if not api_key:
            logger.warning("⚠️ AGI_API_KEY not configured!")
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = "claude-sonnet-4-20250514"
        self.alert_configs = {}
        self.history = {}
        self.max_history_per_child = 1000

    async def score_message(self, message_text: str) -> Dict[str, Any]:
        """
        Score a message using AGI API and return normalized risk dict.
        """
        return await _call_agi_api(message_text)

    async def analyze_message(self, message: str, history: List[Dict] = None) -> ScoreResponse:
        """
        HYBRID ANALYSIS: Rule engine + AGI API
        """
        history = history or []
        # Initialize rule engine if not exists
        if not hasattr(self, 'rule_engine'):
            self.rule_engine = RuleEngine()
            logger.info("✅ Rule engine initialized")
        try:
            # STEP 1: Rule-based analysis (always works)
            rule_result = self.rule_engine.analyze(message, history)
            rule_score = rule_result["score"]
            triggered_rules = rule_result["triggered_rules"]
            logger.info(f"📊 Rule score: {rule_score}, Flags: {triggered_rules}")
            # STEP 2: Try AGI API (fallback if fails)
            try:
                session_id = await self._ensure_session()
                prompt = self._build_grooming_prompt(message)
                agi_response = await self._send_message(session_id, prompt)
                parsed = self._parse_agi_response(agi_response)
                agi_score = parsed.get("risk_score", rule_score) * 10  # Convert 0-10 to 0-100
            except Exception as e:
                logger.warning(f"⚠️  AGI API unavailable, using rule-only: {e}")
                agi_score = rule_score
            # STEP 3: Aggregate scores (60% rules, 40% AGI)
            final_score = aggregate_risk(rule_score, agi_score)
            risk_level_str = classify_risk_level(final_score)
            # Convert to 0-10 scale for response
            final_score_scaled = final_score / 10.0
            # STEP 4: Generate advisory
            advisory = None
            if risk_level_str == "HIGH":
                advisory = "This conversation seems very risky. Please talk to a trusted adult right away."
            elif risk_level_str == "MEDIUM":
                advisory = "Be careful with this conversation. Consider talking to a trusted adult."
            # STEP 5: Calculate confidence
            confidence = 0.85 if len(triggered_rules) >= 2 else 0.70
            return ScoreResponse(
                risk_score=float(final_score_scaled),
                risk_level=RiskLevel(risk_level_str.lower() if risk_level_str != "MEDIUM" else "caution"),
                red_flags=triggered_rules,
                advisory_message=advisory,
                confidence=confidence,
                should_block=final_score >= 70.0
            )
        except Exception as e:
            logger.error(f"❌ Critical error: {e}", exc_info=True)
            return ScoreResponse(
                risk_score=0.0,
                risk_level=RiskLevel.SAFE,
                red_flags=[],
                advisory_message=None,
                confidence=0.0,
                should_block=False
            )
        self.history = {}
        self.max_history_per_child = 1000

    async def initialize(self):
        pass

    async def cleanup(self):
        pass

    # All methods below are now properly indented inside AGIScorer
