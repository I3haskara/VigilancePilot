"""
Rule-based validation engine for API specifications and tests.
"""

from typing import List, Dict, Any, Optional
import re

from vigilancepilot.models import ValidationResult, Severity, IssueType, APIEndpoint


class RulesEngine:
    """
    Rule-based validation engine that performs deterministic checks
    on API specifications and test configurations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the rules engine.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.rules_enabled = self.config.get("rules", {})
    
    def validate_endpoint(self, endpoint: APIEndpoint) -> List[ValidationResult]:
        """
        Validate an API endpoint against all rules.
        
        Args:
            endpoint: The API endpoint to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        if self.rules_enabled.get("check_auth", True):
            results.extend(self._check_authentication(endpoint))
        
        if self.rules_enabled.get("check_rate_limits", True):
            results.extend(self._check_rate_limits(endpoint))
        
        if self.rules_enabled.get("check_error_handling", True):
            results.extend(self._check_error_handling(endpoint))
        
        return results
    
    def _check_authentication(self, endpoint: APIEndpoint) -> List[ValidationResult]:
        """Check if endpoint has proper authentication."""
        results = []
        
        # Check if auth is required and properly configured
        if not endpoint.auth_required:
            results.append(ValidationResult(
                requirement_id="auth_001",
                name="Authentication Required",
                passed=False,
                confidence=0.95,
                severity=Severity.HIGH,
                issue_type=IssueType.AUTH_MISSING,
                issue_description=f"Endpoint {endpoint.method} {endpoint.path} does not require authentication",
                recommendations=[
                    "Add authentication requirement to the endpoint",
                    "Consider using OAuth 2.0, JWT, or API key authentication"
                ]
            ))
        else:
            results.append(ValidationResult(
                requirement_id="auth_001",
                name="Authentication Required",
                passed=True,
                confidence=1.0,
                severity=Severity.HIGH
            ))
        
        return results
    
    def _check_rate_limits(self, endpoint: APIEndpoint) -> List[ValidationResult]:
        """Check if endpoint has rate limiting configured."""
        results = []
        
        if not endpoint.rate_limited:
            results.append(ValidationResult(
                requirement_id="rate_001",
                name="Rate Limiting",
                passed=False,
                confidence=0.85,
                severity=Severity.MEDIUM,
                issue_type=IssueType.RATE_LIMIT_MISSING,
                issue_description=f"Endpoint {endpoint.method} {endpoint.path} does not have rate limiting",
                recommendations=[
                    "Implement rate limiting to prevent abuse",
                    "Consider using sliding window or token bucket algorithm",
                    "Add rate limit headers (X-RateLimit-*) to responses"
                ]
            ))
        else:
            results.append(ValidationResult(
                requirement_id="rate_001",
                name="Rate Limiting",
                passed=True,
                confidence=1.0,
                severity=Severity.MEDIUM
            ))
        
        return results
    
    def _check_error_handling(self, endpoint: APIEndpoint) -> List[ValidationResult]:
        """Check if endpoint has proper error handling."""
        results = []
        
        # Check for common error response codes
        expected_error_codes = ["400", "401", "403", "404", "500"]
        documented_codes = set(endpoint.responses.keys())
        missing_codes = set(expected_error_codes) - documented_codes
        
        if missing_codes:
            results.append(ValidationResult(
                requirement_id="error_001",
                name="Error Response Documentation",
                passed=False,
                confidence=0.90,
                severity=Severity.LOW,
                issue_type=IssueType.ERROR_HANDLING_POOR,
                issue_description=f"Endpoint {endpoint.method} {endpoint.path} is missing error responses: {', '.join(missing_codes)}",
                recommendations=[
                    f"Document error responses for status codes: {', '.join(missing_codes)}",
                    "Include error response schemas with error codes and messages",
                    "Follow consistent error response format across all endpoints"
                ]
            ))
        else:
            results.append(ValidationResult(
                requirement_id="error_001",
                name="Error Response Documentation",
                passed=True,
                confidence=1.0,
                severity=Severity.LOW
            ))
        
        return results
    
    def validate_collection(self, collection: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate a Postman collection structure.
        
        Args:
            collection: Postman collection data
            
        Returns:
            List of validation results
        """
        results = []
        
        # Check collection has items
        items = collection.get("item", [])
        if not items:
            results.append(ValidationResult(
                requirement_id="coll_001",
                name="Collection Has Tests",
                passed=False,
                confidence=1.0,
                severity=Severity.CRITICAL,
                issue_type=IssueType.OTHER,
                issue_description="Collection has no test items",
                recommendations=["Add at least one test request to the collection"]
            ))
        
        # Check for collection-level auth
        auth = collection.get("auth")
        if not auth:
            results.append(ValidationResult(
                requirement_id="coll_002",
                name="Collection Authentication",
                passed=False,
                confidence=0.8,
                severity=Severity.MEDIUM,
                issue_type=IssueType.AUTH_MISSING,
                issue_description="Collection does not have default authentication configured",
                recommendations=[
                    "Configure collection-level authentication",
                    "This will be inherited by all requests"
                ]
            ))
        
        return results
    
    def check_security_patterns(self, text: str) -> List[ValidationResult]:
        """
        Check for common security anti-patterns in API specifications.
        
        Args:
            text: Text to analyze (could be docs, code, etc.)
            
        Returns:
            List of validation results
        """
        results = []
        
        # Check for hardcoded credentials
        credential_patterns = [
            (r'password\s*=\s*["\'][\w]+["\']', "Hardcoded password detected"),
            (r'api[_-]?key\s*=\s*["\'][\w]+["\']', "Hardcoded API key detected"),
            (r'secret\s*=\s*["\'][\w]+["\']', "Hardcoded secret detected"),
        ]
        
        for pattern, message in credential_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                results.append(ValidationResult(
                    requirement_id="sec_001",
                    name="No Hardcoded Credentials",
                    passed=False,
                    confidence=0.95,
                    severity=Severity.CRITICAL,
                    issue_type=IssueType.SECURITY_VULNERABILITY,
                    issue_description=message,
                    recommendations=[
                        "Remove hardcoded credentials",
                        "Use environment variables or secret management systems",
                        "Never commit credentials to version control"
                    ]
                ))
        
        return results
