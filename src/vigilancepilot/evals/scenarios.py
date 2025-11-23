"""
Pre-defined test and evaluation scenarios for VigilancePilot.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from vigilancepilot.models import (
    Requirement, 
    Severity, 
    IssueType, 
    APIEndpoint,
    ValidationResult
)
from vigilancepilot.config import Config


# Define standard evaluation scenarios
SCENARIOS = {
    "basic_auth": {
        "name": "Basic Authentication Test",
        "description": "Validate basic authentication patterns",
        "requirements": [
            Requirement(
                id="auth_basic_001",
                name="API Key Present",
                description="Verify API key authentication is configured",
                severity=Severity.HIGH,
                enabled=True
            ),
            Requirement(
                id="auth_basic_002",
                name="Authorization Header",
                description="Check for Authorization header in requests",
                severity=Severity.HIGH,
                enabled=True
            )
        ]
    },
    "rate_limiting": {
        "name": "Rate Limiting Test",
        "description": "Validate rate limiting implementation",
        "requirements": [
            Requirement(
                id="rate_basic_001",
                name="Rate Limit Headers",
                description="Verify rate limit headers are present",
                severity=Severity.MEDIUM,
                enabled=True
            ),
            Requirement(
                id="rate_basic_002",
                name="429 Response Handling",
                description="Check for proper 429 Too Many Requests handling",
                severity=Severity.MEDIUM,
                enabled=True
            )
        ]
    },
    "error_handling": {
        "name": "Error Handling Test",
        "description": "Validate error response patterns",
        "requirements": [
            Requirement(
                id="error_001",
                name="Standard Error Format",
                description="Verify consistent error response format",
                severity=Severity.LOW,
                enabled=True
            ),
            Requirement(
                id="error_002",
                name="Error Code Coverage",
                description="Check coverage of 4xx and 5xx error codes",
                severity=Severity.MEDIUM,
                enabled=True
            )
        ]
    },
    "security_best_practices": {
        "name": "Security Best Practices",
        "description": "Validate security implementation",
        "requirements": [
            Requirement(
                id="sec_001",
                name="HTTPS Only",
                description="Verify all endpoints use HTTPS",
                severity=Severity.CRITICAL,
                enabled=True
            ),
            Requirement(
                id="sec_002",
                name="No Sensitive Data in URLs",
                description="Check that sensitive data is not in query params",
                severity=Severity.HIGH,
                enabled=True
            ),
            Requirement(
                id="sec_003",
                name="Input Validation",
                description="Verify input validation is documented",
                severity=Severity.HIGH,
                enabled=True
            )
        ]
    },
    "comprehensive": {
        "name": "Comprehensive Validation",
        "description": "Run all validation checks",
        "requirements": []  # Will include all requirements from other scenarios
    }
}


def get_scenario(scenario_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a scenario by name.
    
    Args:
        scenario_name: Name of the scenario
        
    Returns:
        Scenario configuration or None
    """
    return SCENARIOS.get(scenario_name)


def list_scenarios() -> List[str]:
    """
    List all available scenarios.
    
    Returns:
        List of scenario names
    """
    return list(SCENARIOS.keys())


def run_scenario(scenario_name: str, config: Config) -> Dict[str, Any]:
    """
    Run a specific evaluation scenario.
    
    Args:
        scenario_name: Name of the scenario to run
        config: Application configuration
        
    Returns:
        Scenario results
    """
    scenario = get_scenario(scenario_name)
    
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_name}")
    
    results = {
        "scenario": scenario_name,
        "name": scenario["name"],
        "description": scenario["description"],
        "started_at": datetime.utcnow().isoformat(),
        "requirements": len(scenario["requirements"]),
        "passed": 0,
        "failed": 0,
        "validations": []
    }
    
    # Run validations for each requirement
    for requirement in scenario["requirements"]:
        # Simulate validation (in real implementation, this would call actual validation logic)
        validation = _run_requirement_validation(requirement, config)
        results["validations"].append(validation.model_dump())
        
        if validation.passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    results["completed_at"] = datetime.utcnow().isoformat()
    
    return results


def _run_requirement_validation(requirement: Requirement, config: Config) -> ValidationResult:
    """
    Run validation for a single requirement.
    
    Args:
        requirement: The requirement to validate
        config: Application configuration
        
    Returns:
        ValidationResult
    """
    # This is a placeholder implementation
    # In a real scenario, this would perform actual validation logic
    
    return ValidationResult(
        requirement_id=requirement.id,
        name=requirement.name,
        passed=True,  # Placeholder - would be actual validation result
        confidence=0.85,
        severity=requirement.severity,
        issue_type=None,
        issue_description=None,
        recommendations=[]
    )


def create_custom_scenario(
    name: str,
    description: str,
    requirements: List[Requirement]
) -> Dict[str, Any]:
    """
    Create a custom evaluation scenario.
    
    Args:
        name: Scenario name
        description: Scenario description
        requirements: List of requirements to check
        
    Returns:
        Custom scenario configuration
    """
    return {
        "name": name,
        "description": description,
        "requirements": requirements
    }


def generate_test_endpoints() -> List[APIEndpoint]:
    """
    Generate sample API endpoints for testing.
    
    Returns:
        List of sample endpoints
    """
    return [
        APIEndpoint(
            path="/api/v1/users",
            method="GET",
            description="List all users",
            auth_required=True,
            rate_limited=True,
            tags=["users", "read"]
        ),
        APIEndpoint(
            path="/api/v1/users/{id}",
            method="GET",
            description="Get user by ID",
            auth_required=True,
            rate_limited=False,
            tags=["users", "read"]
        ),
        APIEndpoint(
            path="/api/v1/users",
            method="POST",
            description="Create new user",
            auth_required=True,
            rate_limited=True,
            tags=["users", "write"]
        ),
        APIEndpoint(
            path="/api/v1/auth/login",
            method="POST",
            description="User login",
            auth_required=False,
            rate_limited=True,
            tags=["auth"]
        ),
        APIEndpoint(
            path="/api/v1/health",
            method="GET",
            description="Health check",
            auth_required=False,
            rate_limited=False,
            tags=["monitoring"]
        )
    ]
