"""
Telnyx Integration for Voice and SMS Notifications
"""
import logging
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import telnyx

load_dotenv()
logger = logging.getLogger(__name__)


class TelnyxHandler:
    """Handle Telnyx voice and SMS notifications"""
    
    def __init__(self):
        """Initialize Telnyx client"""
        self.api_key = os.getenv("TELNYX_API_KEY")
        self.phone_number = os.getenv("TELNYX_PHONE_NUMBER")
        self.connection_id = os.getenv("TELNYX_CONNECTION_ID")
        
        if self.api_key:
            telnyx.api_key = self.api_key
            logger.info("✅ Telnyx initialized")
        else:
            logger.warning("⚠️ Telnyx not configured")
    
    async def send_alert_sms(
        self,
        to_phone: str,
        message: str,
        child_id: str,
        risk_level: str
    ) -> Dict[str, Any]:
        """Send SMS alert to parent"""
        if not self.api_key:
            logger.warning("Telnyx not configured - SMS not sent")
            return {"status": "skipped", "reason": "not_configured"}
        
        try:
            response = telnyx.Message.create(
                from_=self.phone_number,
                to=to_phone,
                text=message
            )
            
            logger.info(f"SMS alert sent to {to_phone} for child {child_id}")
            return {
                "status": "sent",
                "message_id": response.id,
                "to": to_phone
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def initiate_alert_call(
        self,
        to_phone: str,
        child_id: str,
        risk_level: str
    ) -> Dict[str, Any]:
        """Initiate voice call to parent"""
        if not self.api_key or not self.connection_id:
            logger.warning("Telnyx not configured - call not initiated")
            return {"status": "skipped", "reason": "not_configured"}
        
        try:
            call = telnyx.Call.create(
                connection_id=self.connection_id,
                to=to_phone,
                from_=self.phone_number,
                webhook_url=os.getenv("TELNYX_WEBHOOK_URL")
            )
            
            logger.info(f"Call initiated to {to_phone} for child {child_id}")
            return {
                "status": "initiated",
                "call_id": call.call_control_id,
                "to": to_phone
            }
            
        except Exception as e:
            logger.error(f"Failed to initiate call: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def handle_webhook(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Telnyx webhook events"""
        event_type = event_data.get("event_type", "")
        
        logger.info(f"Received Telnyx webhook: {event_type}")
        
        if event_type == "call.initiated":
            return await self._handle_call_initiated(event_data)
        elif event_type == "call.answered":
            return await self._handle_call_answered(event_data)
        elif event_type == "call.hangup":
            return await self._handle_call_hangup(event_data)
        elif event_type == "message.received":
            return await self._handle_message_received(event_data)
        else:
            logger.warning(f"Unhandled webhook event: {event_type}")
            return {"status": "ignored"}
    
    async def _handle_call_initiated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call initiated event"""
        call_control_id = event_data.get("payload", {}).get("call_control_id")
        logger.info(f"Call initiated: {call_control_id}")
        return {"status": "processed"}
    
    async def _handle_call_answered(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call answered event"""
        call_control_id = event_data.get("payload", {}).get("call_control_id")
        
        # Play alert message
        try:
            telnyx.Call.speak(
                call_control_id=call_control_id,
                payload="This is an urgent alert from VigilancePilot. Your child may have received a concerning message. Please check your SMS for details.",
                voice="female",
                language="en-US"
            )
            logger.info(f"Alert message played for call: {call_control_id}")
        except Exception as e:
            logger.error(f"Failed to play message: {e}")
        
        return {"status": "processed"}
    
    async def _handle_call_hangup(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call hangup event"""
        call_control_id = event_data.get("payload", {}).get("call_control_id")
        logger.info(f"Call ended: {call_control_id}")
        return {"status": "processed"}
    
    async def _handle_message_received(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming SMS"""
        message = event_data.get("payload", {})
        from_number = message.get("from", {}).get("phone_number")
        text = message.get("text")
        
        logger.info(f"Received SMS from {from_number}: {text}")
        return {"status": "processed"}
