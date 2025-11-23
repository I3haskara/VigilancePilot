from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class RiskLevel(str, Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGER = "danger"


class ProofLevel(str, Enum):
    """Evidence strength classification"""
    NONE = "none"
    SUSPECTED = "suspected"
    PROBABLE = "probable"
    CONFIRMED = "confirmed"


class ScoreResponse(BaseModel):
    risk_score: float = Field(..., ge=0.0, le=10.0)
    risk_level: RiskLevel
    red_flags: List[str] = Field(default_factory=list)
    advisory_message: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    should_block: bool
    
    # NEW: Proof-based fields
    proof_level: Optional[ProofLevel] = None
    evidence_summary: Optional[str] = None
"""
Pydantic Models for VigilancePilot Child Safety Monitoring
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class MessageAnalysisRequest(BaseModel):
    """Request model for message analysis"""
    message: str = Field(..., description="The message content to analyze")
    child_id: str = Field(..., description="Unique identifier for the child")
    platform: str = Field(..., description="Platform where message was sent (SMS, WhatsApp, Instagram, etc.)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context (sender info, thread, etc.)")
    timestamp: Optional[str] = Field(default=None, description="Message timestamp")


class MessageAnalysisResponse(BaseModel):
    """Response model for message analysis"""
    child_id: str = Field(..., description="Child identifier")
    platform: str = Field(..., description="Platform")
    risk_level: str = Field(..., description="Risk level: safe, low, medium, high, danger")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score 0-100")
    categories_detected: List[str] = Field(default_factory=list, description="Risk categories detected")
    threat_indicators: List[str] = Field(default_factory=list, description="Specific threat indicators found")
    ai_reasoning: str = Field(..., description="AI explanation of the analysis")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence in the analysis")
    recommended_action: str = Field(..., description="Recommended action: log_only, notify_parent, alert_urgent, block_contact")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BatchAnalysisRequest(BaseModel):
    """Request model for batch analysis"""
    messages: List[MessageAnalysisRequest] = Field(..., description="List of messages to analyze")


class AlertConfig(BaseModel):
    """Configuration for alert thresholds"""
    child_id: str
    parent_phone: str
    alert_threshold: str = "medium"  # minimum risk level to trigger alert
    notification_methods: List[str] = ["sms", "call"]
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class HealthCheck(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    agi_api_ready: bool = Field(..., description="AGI API availability")
    telnyx_ready: bool = Field(..., description="Telnyx API availability")
    version: str = Field(default="1.0.0")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WebhookEvent(BaseModel):
    """Telnyx webhook event"""
    event_type: str
    id: str
    occurred_at: str
    payload: Dict[str, Any]


class TelnyxCallRequest(BaseModel):
    """Request to initiate Telnyx call"""
    to_phone: str
    message: str
    child_id: str
    risk_level: str
