"""
Pydantic models for VigilancePilot data structures.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class Severity(str, Enum):
    """Issue severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueType(str, Enum):
    """Types of issues that can be detected."""
    AUTH_MISSING = "auth_missing"
    AUTH_WEAK = "auth_weak"
    RATE_LIMIT_MISSING = "rate_limit_missing"
    ERROR_HANDLING_POOR = "error_handling_poor"
    VALIDATION_MISSING = "validation_missing"
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_ISSUE = "performance_issue"
    DOCUMENTATION_INCOMPLETE = "documentation_incomplete"
    OTHER = "other"


class Requirement(BaseModel):
    """Represents a validation requirement."""
    id: str
    name: str
    description: str
    severity: Severity
    enabled: bool = True
    rule_based: bool = True
    llm_enhanced: bool = False
    
    class Config:
        use_enum_values = True


class TestCase(BaseModel):
    """
    Represents a single API test case for test planning.
    
    Fields:
      - id:            Stable identifier for the test case (e.g., "TC-HAPPY-001").
      - category:      Type of test such as "happy", "negative", "boundary".
      - description:   Human-readable explanation of what this test verifies.
      - steps:         Ordered list of high-level steps the test will perform.
      - expected_result: What we expect the API to return / do.
    """
    id: str
    category: str
    description: str
    steps: List[str]
    expected_result: str


class TestPlan(BaseModel):
    """
    Groups all generated test cases for a single requirement.

    Fields:
      - requirement:      Original natural-language requirement text.
      - generated_cases:  List of concrete TestCase objects derived from it.
    """
    requirement: str
    generated_cases: List[TestCase]


class PostmanTestCase(BaseModel):
    """Represents a single Postman test case (legacy model)."""
    id: str
    name: str
    description: Optional[str] = None
    method: str  # GET, POST, etc.
    url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    assertions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Result of a validation check."""
    requirement_id: str
    name: str
    passed: bool
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Severity
    issue_type: Optional[IssueType] = None
    issue_description: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class RunResult(BaseModel):
    """Result of a test run."""
    run_id: str
    collection_id: str
    collection_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    validations: List[ValidationResult] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if there are critical validation failures."""
        return any(
            not v.passed and v.severity == Severity.CRITICAL 
            for v in self.validations
        )


class PostmanCollection(BaseModel):
    """Represents a Postman collection."""
    id: str
    name: str
    description: Optional[str] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
    variables: List[Dict[str, Any]] = Field(default_factory=list)
    auth: Optional[Dict[str, Any]] = None


class APIEndpoint(BaseModel):
    """Represents an API endpoint for analysis."""
    path: str
    method: str
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    auth_required: bool = True
    rate_limited: bool = False
    tags: List[str] = Field(default_factory=list)
