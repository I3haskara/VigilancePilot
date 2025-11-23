from typing import Optional, Dict, Any

from fastapi import FastAPI
from .schemas import AnalysisRequest
from .agi_scorer import AGIScorer


from typing import Optional, Dict, Any
import os
import math

from fastapi import FastAPI
from pydantic import BaseModel

from .agi_scorer import AGIScorer


import logging

import os
import sys
import logging

# --- make sure we can import from the top-level "backend" folder ---
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# now these modules are in backend/
from rule_engine import RuleEngine
from send_parent_alert_sms import send_parent_alert_sms

logger = logging.getLogger(__name__)


app = FastAPI(title="VigilancePilot API")

# --- CORS FIX ---
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all during hackathon demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialise your rule engine once at startup
rule_engine = RuleEngine()


# ---------- REQUEST MODEL ----------




# ---------- BASIC HEALTH CHECKS ----------

@app.get("/")
def read_root() -> Dict[str, str]:
    return {"status": "ok", "service": "VigilancePilot"}


@app.get("/health", include_in_schema=False)
def health() -> Dict[str, str]:
    return {"status": "healthy"}


# ---------- HELPERS ----------

def _extract_risk_score(agi_result: Dict[str, Any]) -> float:
    """
    Try to pull a numeric risk score out of the AGI response.

    We support multiple possible keys to be robust:
    - 'risk_score'
    - 'score'
    - 'risk' (0–1 or 0–100)
    """
    candidates = [
        agi_result.get("risk_score"),
        agi_result.get("score"),
        agi_result.get("risk"),
    ]

    for value in candidates:
        if value is None:
            continue
        try:
            val = float(value)
            # If it's a 0–1 float, scale to 0–100.
            if 0.0 <= val <= 1.0:
                return val * 100.0
            return val
        except (TypeError, ValueError):
            continue

    return 0.0


async def _send_sms_alert(
    text: str,
    to_phone: str,
) -> Dict[str, Any]:
    """
    Fire-and-forget SMS via Telnyx.
    This is deliberately defensive: any failure returns a status dict
    but does NOT raise, so the API response is never broken by SMS issues.
    """
    api_key = os.getenv("TELNYX_API_KEY")
    messaging_profile_id = os.getenv("TELNYX_MESSAGING_PROFILE_ID")
    from_phone = os.getenv("TELNYX_FROM_NUMBER")

    if not api_key or not messaging_profile_id or not from_phone:
        return {
            "status": "skipped",
            "reason": "Missing TELNYX_API_KEY / TELNYX_MESSAGING_PROFILE_ID / TELNYX_FROM_NUMBER",
        }

    try:
        # Lazy import so missing telnyx package doesn't break startup.
        import telnyx  # type: ignore

        telnyx.api_key = api_key

        msg = telnyx.Message.create(
            messaging_profile_id=messaging_profile_id,
            from_=from_phone,
            to=to_phone,
            text=text,
        )

        return {
            "status": "sent",
            "telnyx_id": getattr(msg, "id", None),
        }

    except ImportError:
        return {
            "status": "failed",
            "reason": "telnyx Python package not installed",
        }
    except Exception as exc:
        return {
            "status": "failed",
            "reason": str(exc),
        }


# ---------- MAIN ANALYZE ENDPOINT (AGI + OPTIONAL SMS) ----------


@app.post("/api/analyze")
async def analyze_api(payload: AnalysisRequest) -> Dict[str, Any]:
    """
    Core demo endpoint:
    - runs rule-based grooming detection
    - optionally calls AGI (if configured)
    - sends SMS if risk is HIGH
    - always returns risk_label, risk_score, alert_sent
    """

    # 1) Run rule engine on the message
    rule_result = rule_engine.analyze_message(
        message=payload.message,
        child_id=payload.child_id,
        platform=payload.platform,
        context=payload.context,
        timestamp=payload.timestamp,
        conversation_id=payload.conversation_id,
    )
    # Expect your rule engine to give something like:
    # {"risk_score": 0.92, "risk_label": "HIGH", "flags": [...]}
    risk_score = float(rule_result.get("risk_score", 0.0))
    risk_label = str(rule_result.get("risk_label", "UNKNOWN")).upper()
    flags = rule_result.get("flags", [])

    # 2) Try AGI scoring, but NEVER fail the endpoint if AGI is broken
    agi_error = None
    agi_extra = None
    try:
        # if you have AGI integration, call it here
        # agi_extra = await agi_client.score_message(payload.message)
        # risk_score = agi_extra.get("risk_score", risk_score)
        # risk_label = agi_extra.get("risk_label", risk_label)
        pass
    except Exception as e:
        agi_error = str(e)
        logger.exception("AGI analysis failed")

    # 3) Decide if we send SMS
    alert_sent = False
    alert_error = None

    try:
        # Demo rule: send SMS only if HIGH risk
        if risk_label == "HIGH":
            sms_payload = {
                "risk_score": risk_score,
                "risk_label": risk_label,
                "flags": flags,
                "child_id": payload.child_id or "demo-child",
                "platform": payload.platform or "demo-ui",
                "message": payload.message,
            }
            await send_parent_alert_sms(sms_payload)
            alert_sent = True
    except Exception as e:
        alert_error = str(e)
        logger.exception("Failed to send parent alert SMS")

    # 4) Return a clean, demo-friendly JSON
    return {
        "input": payload.dict(),
        "risk_score": risk_score,
        "risk_label": risk_label,
        "flags": flags,
        "alert_sent": alert_sent,
        "alert_error": alert_error,
        "agi_error": agi_error,
        "agi_extra": agi_extra,
    }


