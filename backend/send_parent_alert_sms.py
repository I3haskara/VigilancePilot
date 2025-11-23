import httpx
import logging
from typing import Dict, Any
from backend.config import settings

logger = logging.getLogger(__name__)

async def send_parent_alert_sms(risk_payload: Dict[str, Any]) -> None:
    """
    Uses TELNYX_API_KEY, TELNYX_PHONE_NUMBER, PARENT_ALERT_PHONE.
    Calls POST https://api.telnyx.com/v2/messages with JSON:
      {
        "from": TELNYX_PHONE_NUMBER,
        "to": PARENT_ALERT_PHONE,
        "text": "<short alert text>"
      }
    Should log errors but NEVER raise exceptions that crash the API.
    """
    telnyx_api_key = settings.TELNYX_API_KEY
    telnyx_phone = settings.TELNYX_PHONE_NUMBER
    parent_phone = settings.PARENT_ALERT_PHONE
    alert_text = risk_payload.get("text", "VigilancePilot Alert: Risk detected.")

    if not telnyx_api_key or not telnyx_phone or not parent_phone:
        logger.warning("Telnyx SMS config missing; alert not sent.")
        return

    url = "https://api.telnyx.com/v2/messages"
    headers = {
        "Authorization": f"Bearer {telnyx_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": telnyx_phone,
        "to": parent_phone,
        "text": alert_text
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            logger.info(f"Parent SMS alert sent: {parent_phone} | {alert_text}")
    except Exception as e:
        logger.error(f"Failed to send parent SMS alert: {e}")
        # Never raise exception
