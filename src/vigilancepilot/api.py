from typing import Optional, Dict, Any

from fastapi import FastAPI
from pydantic import BaseModel

from .agi_scorer import AGIScorer


from typing import Optional, Dict, Any
import os
import math

from fastapi import FastAPI
from pydantic import BaseModel

from .agi_scorer import AGIScorer


app = FastAPI(
    title="VigilancePilot API",
    version="0.2.0",
    description="VigilancePilot – AGI-powered grooming risk analysis with SMS alerts",
)


# ---------- REQUEST MODEL ----------

class AnalysisRequest(BaseModel):
    message: str
    child_id: Optional[str] = None
    platform: Optional[str] = None
    timestamp: Optional[str] = None
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    # optional: override default alert phone
    alert_phone: Optional[str] = None


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
async def analyze(req: AnalysisRequest) -> Dict[str, Any]:
    """
    Run AGI analysis on a single chat message and, if the risk is high,
    send an SMS alert to the parent / guardian.

    Risk → SMS logic:
    - Extract risk score from AGI result (0–100).
    - If score >= ALERT_THRESHOLD, send SMS using Telnyx.
    - SMS failures are reported in 'sms_status' but never cause a 500.
    """
    ALERT_THRESHOLD = 70.0  # adjust as needed

    # 1) Initialize AGI scorer (safe / defensive)
    try:
        agi_scorer = AGIScorer()
    except Exception as exc:
        return {
            "input": req.dict(),
            "error": "AGI scorer could not be initialized",
            "detail": str(exc),
        }

    # 2) Run AGI analysis
    try:
        agi_result = await agi_scorer.analyze_text(req.message)
    except Exception as exc:
        return {
            "input": req.dict(),
            "error": "AGI analysis failed",
            "detail": str(exc),
        }

    # 3) Compute risk score
    risk_score = _extract_risk_score(agi_result)
    risk_score_rounded = float(f"{risk_score:.2f}")
    risk_level = "low"
    if risk_score_rounded >= ALERT_THRESHOLD:
        risk_level = "high"
    elif risk_score_rounded >= ALERT_THRESHOLD * 0.5:
        risk_level = "medium"

    # 4) Decide whether to send SMS
    sms_status: Dict[str, Any] = {
        "status": "not_triggered",
        "reason": "risk below threshold",
    }

    if risk_score_rounded >= ALERT_THRESHOLD:
        # Figure out where to send the alert
        to_phone = (
            req.alert_phone
            or os.getenv("TELNYX_ALERT_PHONE")
            or os.getenv("PARENT_ALERT_PHONE", "")
        )

        if to_phone:
            # Compose concise alert text
            preview = req.message.strip().replace("\n", " ")
            if len(preview) > 120:
                preview = preview[:117] + "..."

            sms_text = (
                f"[VigilancePilot] HIGH RISK ({math.floor(risk_score_rounded)}). "
                f"Child: {req.child_id or 'unknown'}, "
                f"Platform: {req.platform or 'unknown'}. "
                f"Message: \"{preview}\""
            )

            sms_status = await _send_sms_alert(
                text=sms_text,
                to_phone=to_phone,
            )
        else:
            sms_status = {
                "status": "skipped",
                "reason": "No alert phone configured (TELNYX_ALERT_PHONE / PARENT_ALERT_PHONE / request.alert_phone)",
            }

    # 5) Return combined response
    return {
        "input": req.dict(),
        "agi_result": agi_result,
        "risk_score": risk_score_rounded,
        "risk_level": risk_level,
        "alert_threshold": ALERT_THRESHOLD,
        "sms_status": sms_status,
    }


