from fastapi import Request
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def handle_telnyx_webhook(request: Request) -> Dict[str, Any]:
    try:
        payload = await request.json()
        logger.info(f"Received Telnyx webhook payload: {payload}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error parsing Telnyx webhook: {e}")
        return {"status": "error", "detail": str(e)}
