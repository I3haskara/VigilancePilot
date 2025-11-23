from pydantic import BaseModel
from typing import Optional, Any

class AnalysisRequest(BaseModel):
    message: str  # this is the only required field for now
    child_id: Optional[str] = None
    platform: Optional[str] = None
    timestamp: Optional[str] = None
    context: Optional[Any] = None
    conversation_id: Optional[str] = None
