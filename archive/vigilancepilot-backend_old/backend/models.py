"""
Pydantic Models for VigilancePilot API
Data validation and schema definitions
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Any, List, Optional
from datetime import datetime


class HealthCheck(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Health status: healthy, degraded, or unhealthy")
    agi_scorer_ready: bool = Field(..., description="AGI scorer availability")
    version: str = Field(..., description="API version")


class ValidationResult(BaseModel):
    """API validation result"""
    is_valid: bool = Field(..., description="Whether the response is valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    agi_score: float = Field(..., ge=0, le=100, description="AGI validation score (0-100)")
    agi_feedback: str = Field(..., description="AGI-generated feedback")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for improvement"
    )


class APITestRequest(BaseModel):
    """Request model for API testing"""
    url: str = Field(..., description="API endpoint URL to test")
    method: str = Field(
        default="GET",
        description="HTTP method (GET, POST, PUT, DELETE, etc.)"
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Request headers"
    )
    body: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Request body for POST/PUT requests"
    )
    expected_status: int = Field(
        default=200,
        description="Expected HTTP status code"
    )
    validation_rules: Optional[List[str]] = Field(
        default=None,
        description="Custom validation rules to apply"
    )
    timeout: Optional[int] = Field(
        default=30,
        description="Request timeout in seconds"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://api.example.com/users/123",
                "method": "GET",
                "headers": {
                    "Authorization": "Bearer token123",
                    "Content-Type": "application/json"
                },
                "expected_status": 200,
                "validation_rules": [
                    "Response must contain 'id' field",
                    "Response time must be under 1 second"
                ]
            }
        }


class APITestResponse(BaseModel):
    """Response model for API test results"""
    success: bool = Field(..., description="Whether the test succeeded")
    status_code: int = Field(..., description="HTTP status code received")
    response_data: Dict[str, Any] = Field(..., description="API response body")
    response_time: float = Field(..., description="Response time in seconds")
    validation: ValidationResult = Field(..., description="Validation results")
    timestamp: str = Field(..., description="Test execution timestamp (ISO format)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "status_code": 200,
                "response_data": {
                    "id": 123,
                    "name": "John Doe",
                    "email": "john@example.com"
                },
                "response_time": 0.342,
                "validation": {
                    "is_valid": True,
                    "errors": [],
                    "warnings": ["Consider adding pagination"],
                    "agi_score": 95.0,
                    "agi_feedback": "Response is well-structured and complete",
                    "recommendations": ["Add rate limiting headers"]
                },
                "timestamp": "2025-11-22T12:00:00Z"
            }
        }


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown"""
    correctness: float = Field(..., ge=0, le=100, description="Correctness score")
    completeness: float = Field(..., ge=0, le=100, description="Completeness score")
    performance: float = Field(..., ge=0, le=100, description="Performance score")
    security: float = Field(..., ge=0, le=100, description="Security score")
    usability: float = Field(..., ge=0, le=100, description="Usability score")


class AGIScoreRequest(BaseModel):
    """Request model for AGI scoring"""
    endpoint: str = Field(..., description="API endpoint being scored")
    response_data: Dict[str, Any] = Field(..., description="API response to score")
    expected_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Expected response schema"
    )
    context: Optional[str] = Field(
        default=None,
        description="Additional context for scoring"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "/api/users/123",
                "response_data": {
                    "id": 123,
                    "name": "John Doe",
                    "email": "john@example.com"
                },
                "expected_schema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    }
                },
                "context": "User profile endpoint for authenticated users"
            }
        }


class AGIScoreResponse(BaseModel):
    """Response model for AGI scoring"""
    endpoint: str = Field(..., description="Endpoint that was scored")
    overall_score: float = Field(..., ge=0, le=100, description="Overall score (0-100)")
    breakdown: ScoreBreakdown = Field(..., description="Detailed score breakdown")
    feedback: str = Field(..., description="Detailed AGI feedback")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Improvement recommendations"
    )
    timestamp: str = Field(..., description="Scoring timestamp (ISO format)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "/api/users/123",
                "overall_score": 92.0,
                "breakdown": {
                    "correctness": 95.0,
                    "completeness": 90.0,
                    "performance": 88.0,
                    "security": 92.0,
                    "usability": 95.0
                },
                "feedback": "The API response is well-structured with good security practices...",
                "recommendations": [
                    "Consider adding HATEOAS links",
                    "Add response compression",
                    "Include rate limit headers"
                ],
                "timestamp": "2025-11-22T12:00:00Z"
            }
        }


class BatchTestRequest(BaseModel):
    """Request model for batch testing"""
    tests: List[APITestRequest] = Field(..., description="List of API tests to run")
    parallel: bool = Field(default=True, description="Whether to run tests in parallel")
    stop_on_failure: bool = Field(
        default=False,
        description="Stop execution if any test fails"
    )


class BatchTestResponse(BaseModel):
    """Response model for batch testing"""
    total: int = Field(..., description="Total number of tests")
    passed: int = Field(..., description="Number of passed tests")
    failed: int = Field(..., description="Number of failed tests")
    results: List[APITestResponse] = Field(..., description="Individual test results")
    duration: float = Field(..., description="Total execution time in seconds")
    timestamp: str = Field(..., description="Batch execution timestamp (ISO format)")


class TestHistory(BaseModel):
    """Historical test record"""
    test_id: str = Field(..., description="Unique test identifier")
    url: str = Field(..., description="Tested endpoint URL")
    method: str = Field(..., description="HTTP method used")
    success: bool = Field(..., description="Test result")
    agi_score: float = Field(..., description="AGI score received")
    timestamp: str = Field(..., description="Test execution timestamp (ISO format)")


class SystemStats(BaseModel):
    """System statistics"""
    total_tests: int = Field(..., description="Total tests executed")
    average_score: float = Field(..., description="Average AGI score")
    success_rate: float = Field(..., description="Success rate percentage")
    uptime: float = Field(..., description="System uptime in seconds")
    last_test: Optional[str] = Field(None, description="Last test timestamp")
