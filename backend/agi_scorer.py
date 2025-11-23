import os
import httpx

AGI_API_KEY = os.getenv("AGI_API_KEY")
AGI_ASSISTANT_ID = os.getenv("AGI_ASSISTANT_ID")


class AGIScorer:
    """
    Handles sending text to AGI.tech, receiving analysis,
    and normalizing the output into a structured risk result.
    """

    def __init__(self):
        if not AGI_API_KEY:
            raise ValueError("Missing AGI_API_KEY in environment variables")

        if not AGI_ASSISTANT_ID:
            raise ValueError("Missing AGI_ASSISTANT_ID in environment variables")

        self.base_url = "https://api.agi.tech/v1"

    async def analyze_text(self, text: str) -> dict:
        """
        Sends the message to AGI.tech and retrieves structured analysis.
        """
        url = f"{self.base_url}/assistants/{AGI_ASSISTANT_ID}/messages"

        headers = {
            "Authorization": f"Bearer {AGI_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "messages": [{"role": "user", "content": text}],
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)

        response.raise_for_status()
        raw = response.json()
        return self._normalize_response(raw)

    def _normalize_response(self, raw: dict) -> dict:
        """
        Convert AGI output into our standardized result format.
        """
        try:
            content = raw["messages"][0]["content"]
        except Exception:
            content = "Could not extract content"

        return {
            "agi_raw": raw,
            "agi_summary": content,
            "risk_score": self._compute_risk(content),
        }

    def _compute_risk(self, text: str) -> int:
        """
        Converts AGI summary into a simple threat score.
        This will later merge with heuristic scoring.
        """
        text = text.lower()

        high_risk_terms = ["grooming", "sexual", "meet up", "secret", "don't tell"]
        medium_terms = ["alone", "private", "location"]

        score = 0

        if any(t in text for t in high_risk_terms):
            score += 70
        if any(t in text for t in medium_terms):
            score += 30

        return min(score, 100)
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
            # Keep this empty for now. Later you can add:
            # - API keys
            # - base_url
            # - httpx.Client, etc.

        def analyze_message(
            self,
            message: str,
            child_id: Optional[str] = None,
            platform: Optional[str] = None,
            context: Optional[Dict[str, Any]] = None,
            timestamp: Optional[str] = None,
            conversation_id: Optional[str] = None,
        ) -> Dict[str, Any]:
            """
            Analyze a message and return a normalized risk dict.

            Returns:
                {
                    "risk_score": float (0–100),
                    "risk_level": "low" | "medium" | "high",
                    "reason": str,
                    "message": str,
                    "child_id": Optional[str],
                    "platform": Optional[str],
                    "context": dict,
                    "timestamp": Optional[str],
                    "conversation_id": Optional[str],
                }
            """
            text = (message or "").lower()
            context = context or {}

            # ---- baseline ----
            score: float = 5.0
            reasons = []

            # ---- simple heuristic patterns ----
            patterns = [
                ("keep this secret", 85, "Asking the child to keep secrets"),
                ("don't tell your parents", 90, "Discouraging disclosure to parents"),
                ("dont tell your parents", 90, "Discouraging disclosure to parents"),
                ("meet you alone", 80, "Request to meet alone"),
                ("meet alone", 75, "Request to meet alone"),
                ("come over when your parents are out", 90, "Request to meet unsupervised"),
                ("send me a picture", 70, "Request for pictures"),
                ("send me a pic", 70, "Request for pictures"),
                ("delete this chat", 75, "Request to hide the conversation"),
                ("this is our little secret", 90, "Secret-keeping language"),
            ]

            for phrase, extra_score, why in patterns:
                if phrase in text:
                    score = max(score, extra_score)
                    reasons.append(why)

            # Slightly more generic heuristic
            if "meet" in text and "alone" in text:
                score = max(score, 65)
                reasons.append("Mentions of meeting alone")

            # Clamp to [0, 100]
            score = max(0.0, min(100.0, float(score)))

            # ---- map score → level ----
            if score >= 75.0:
                level = "high"
            elif score >= 40.0:
                level = "medium"
            else:
                level = "low"

            if not reasons:
                reasons.append(
                    "No explicit grooming language detected. Baseline low risk only."
                )

            return {
                "risk_score": score,
                "risk_level": level,
                "reason": "; ".join(reasons),
                "message": message,
                "child_id": child_id,
                "platform": platform,
                "context": context,
                "timestamp": timestamp,
                "conversation_id": conversation_id,
            }
    async def score_message(self, message_text: str) -> Dict[str, Any]:
        """
        Score a message using AGI API and return normalized risk dict.
        """
        return await _call_agi_api(message_text)

    def analyze_message(
        self,
        message: str,
        child_id: str,
        platform: str,
    ) -> dict:
        """
        Minimal, stable contract for AGI risk scoring.
        Only message + metadata it actually uses.
        """
        # Example — replace with your real AGI call
        result = self.model.predict({
            "message": message,
            "child_id": child_id,
            "platform": platform,
        })

        # Normalise into a dict with clear keys
        return {
            "risk_score": float(result["risk_score"]),
            "risk_level": result.get("risk_level", "unknown"),
            "reason": result.get("reason", ""),
        }
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
