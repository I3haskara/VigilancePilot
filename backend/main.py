from .handle_telnyx_webhook import handle_telnyx_webhook
"""
VigilancePilot FastAPI Backend - Child Safety Monitoring
Main application entry point
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any, List
import os
from datetime import datetime

from .models import (
    MessageAnalysisRequest,
    MessageAnalysisResponse,
    BatchAnalysisRequest,
    AlertConfig,
    HealthCheck,
    WebhookEvent,
)
from .agi_scorer import AGIScorer
from .telnyx_handler import TelnyxHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
agi_scorer: AGIScorer = None
telnyx_handler: TelnyxHandler = None
active_websockets: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global agi_scorer, telnyx_handler
    
    # Startup
    logger.info("🚀 Starting VigilancePilot Backend...")
    agi_scorer = AGIScorer()
    await agi_scorer.initialize()
    
    telnyx_handler = TelnyxHandler()
    
    logger.info("✅ VigilancePilot ready for child safety monitoring")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down VigilancePilot...")
    if agi_scorer:
        await agi_scorer.cleanup()


# Initialize FastAPI app
app = FastAPI(
    title="VigilancePilot API",
    description="Child Safety Monitoring with AGI-Powered Grooming Detection",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "VigilancePilot API",
        "version": "1.0.0",
        "description": "Child Safety Monitoring with AGI-Powered Grooming Detection",
        "status": "operational",
        "endpoints": {
            "analyze": "POST /api/analyze",
            "batch": "POST /api/batch-analyze",
            "health": "GET /health",
            "webhooks": "POST /webhooks/telnyx"
        }
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    agi_ready = await agi_scorer.check_health() if agi_scorer else False
    telnyx_ready = bool(telnyx_handler and telnyx_handler.api_key)
    
    return HealthCheck(
        status="healthy" if (agi_ready or telnyx_ready) else "degraded",
        agi_api_ready=agi_ready,
        telnyx_ready=telnyx_ready,
        version="1.0.0"
    )



@app.post("/api/analyze", response_model=MessageAnalysisResponse)
async def analyze_message(req: MessageAnalysisRequest):
    """
    FLOW:
      1. Call risk engine / agi_scorer with the request.
      2. Build MessageAnalysisResponse.
      3. If risk_level is "medium" or "high", trigger Telnyx SMS.
    """
    try:
        logger.info(f"Analyzing message from child_id: {req.child_id}")
        # 1. Call risk engine
        result = await agi_scorer.analyze_message(
            message=req.message,
            context=req.context,
            child_id=req.child_id,
            platform=req.platform
        )
        logger.info(f"Analysis complete - Risk: {result.risk_level} ({result.risk_score}/100)")

        # 2. If risk_level is medium/high, trigger Telnyx SMS
        if result.risk_level in {"medium", "high"}:
            from send_parent_alert_sms import send_parent_alert_sms
            await send_parent_alert_sms(result.model_dump())

        # Broadcast to websocket clients
        await _broadcast_alert(result)
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/batch-analyze", response_model=List[MessageAnalysisResponse])
async def batch_analyze(request: BatchAnalysisRequest):
    """
    Analyze multiple messages in batch
    
    Args:
        request: Batch analysis request with list of messages
    
    Returns:
        List of analysis results
    """
    try:
        logger.info(f"Batch analyzing {len(request.messages)} messages")
        
        results = []
        for msg_request in request.messages:
            result = await agi_scorer.analyze_message(
                message=msg_request.message,
                context=msg_request.context,
                child_id=msg_request.child_id,
                platform=msg_request.platform
            )
            results.append(result)
        
        logger.info(f"Batch analysis complete: {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@app.post("/webhooks/telnyx")
async def telnyx_webhook(event: WebhookEvent):
    """
    Handle Telnyx webhook events
    
    Args:
        event: Telnyx webhook event data
    
    Returns:
        Acknowledgment
    """
    try:
        logger.info(f"Received Telnyx webhook: {event.event_type}")
        
        result = await telnyx_handler.handle_webhook(event.dict())
        
        return {"status": "received", "result": result}
        
    except Exception as e:
        logger.error(f"Webhook handling failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Webhook failed: {str(e)}")


@app.post("/api/alert/configure")
async def configure_alert(config: AlertConfig):
    """
    Configure alert settings for a child
    
    Args:
        config: Alert configuration with thresholds and notification preferences
    
    Returns:
        Confirmation
    """
    try:
        agi_scorer.configure_alert(config)
        return {
            "status": "configured",
            "child_id": config.child_id,
            "alert_threshold": config.alert_threshold
        }
        
    except Exception as e:
        logger.error(f"Alert configuration failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/{child_id}")
async def get_history(child_id: str, limit: int = 50):
    """
    Get analysis history for a child
    
    Args:
        child_id: Child identifier
        limit: Maximum number of results
    
    Returns:
        List of historical analyses
    """
    try:
        history = await agi_scorer.get_history(child_id, limit)
        return {
            "child_id": child_id,
            "count": len(history),
            "history": history
        }
        
    except Exception as e:
        logger.error(f"History retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alerts
    """
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            await websocket.send_json({"status": "connected"})
            
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        logger.info("WebSocket client disconnected")


async def _send_alert(config: AlertConfig, result: MessageAnalysisResponse):
    """Send alert to parent via configured methods"""
    message = f"""
⚠️ VIGILANCEPILOT ALERT

Child ID: {result.child_id}
Risk Level: {result.risk_level.upper()}
Risk Score: {result.risk_score}/100

Threat Indicators:
{chr(10).join(f"• {indicator}" for indicator in result.threat_indicators)}

Platform: {result.platform}
Time: {result.timestamp}

AI Analysis: {result.ai_reasoning}

Please review your child's messages immediately.
"""
    
    if "sms" in config.notification_methods:
        await telnyx_handler.send_alert_sms(
            to_phone=config.parent_phone,
            message=message,
            child_id=result.child_id,
            risk_level=result.risk_level
        )
    
    if "call" in config.notification_methods and result.risk_level in ["high", "danger"]:
        await telnyx_handler.initiate_alert_call(
            to_phone=config.parent_phone,
            child_id=result.child_id,
            risk_level=result.risk_level
        )


async def _broadcast_alert(result: MessageAnalysisResponse):
    """Broadcast alert to connected WebSocket clients"""
    if not active_websockets:
        return
    
    message = {
        "type": "alert",
        "data": result.dict()
    }
    
    for websocket in active_websockets[:]:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            active_websockets.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
