"""
Tests for the rules engine.
"""

import pytest
from vigilancepilot.models import APIEndpoint, Severity, IssueType
from vigilancepilot.detection.rules_engine import RulesEngine


class TestRulesEngine:
    """Test cases for RulesEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RulesEngine()
    
    def test_authentication_check_pass(self):
        """Test that authentication check passes for secured endpoint."""
        endpoint = APIEndpoint(
            path="/api/v1/users",
            method="GET",
            auth_required=True,
            rate_limited=False
        )
        
        results = self.engine._check_authentication(endpoint)
        
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].requirement_id == "auth_001"
    
    def test_authentication_check_fail(self):
        """Test that authentication check fails for unsecured endpoint."""
        endpoint = APIEndpoint(
            path="/api/v1/users",
            method="GET",
            auth_required=False,
            rate_limited=False
        )
        
        results = self.engine._check_authentication(endpoint)
        
        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].severity == Severity.HIGH
        assert results[0].issue_type == IssueType.AUTH_MISSING
    
    def test_rate_limiting_check_pass(self):
        """Test that rate limiting check passes."""
        endpoint = APIEndpoint(
            path="/api/v1/users",
            method="POST",
            auth_required=True,
            rate_limited=True
        )
        
        results = self.engine._check_rate_limits(endpoint)
        
        assert len(results) == 1
        assert results[0].passed is True
    
    def test_rate_limiting_check_fail(self):
        """Test that rate limiting check fails."""
        endpoint = APIEndpoint(
            path="/api/v1/users",
            method="POST",
            auth_required=True,
            rate_limited=False
        )
        
        results = self.engine._check_rate_limits(endpoint)
        
        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].severity == Severity.MEDIUM
        assert results[0].issue_type == IssueType.RATE_LIMIT_MISSING
    
    def test_error_handling_check_pass(self):
        """Test error handling check with complete error responses."""
        endpoint = APIEndpoint(
            path="/api/v1/users",
            method="GET",
            auth_required=True,
            rate_limited=False,
            responses={
                "200": {"description": "Success"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "500": {"description": "Internal Server Error"}
            }
        )
        
        results = self.engine._check_error_handling(endpoint)
        
        assert len(results) == 1
        assert results[0].passed is True
    
    def test_error_handling_check_fail(self):
        """Test error handling check with missing error responses."""
        endpoint = APIEndpoint(
            path="/api/v1/users",
            method="GET",
            auth_required=True,
            rate_limited=False,
            responses={
                "200": {"description": "Success"}
            }
        )
        
        results = self.engine._check_error_handling(endpoint)
        
        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].issue_type == IssueType.ERROR_HANDLING_POOR
    
    def test_validate_endpoint(self):
        """Test full endpoint validation."""
        endpoint = APIEndpoint(
            path="/api/v1/users",
            method="GET",
            auth_required=True,
            rate_limited=True,
            responses={
                "200": {"description": "Success"},
                "400": {"description": "Bad Request"},
                "401": {"description": "Unauthorized"},
                "403": {"description": "Forbidden"},
                "404": {"description": "Not Found"},
                "500": {"description": "Internal Server Error"}
            }
        )
        
        results = self.engine.validate_endpoint(endpoint)
        
        # Should have results for auth, rate limiting, and error handling
        assert len(results) >= 3
        assert all(r.passed for r in results)
    
    def test_validate_collection_empty(self):
        """Test collection validation with empty collection."""
        collection = {"item": []}
        
        results = self.engine.validate_collection(collection)
        
        # Should fail because collection has no items
        assert any(not r.passed for r in results)
        assert any(r.requirement_id == "coll_001" for r in results)
    
    def test_validate_collection_no_auth(self):
        """Test collection validation without auth."""
        collection = {
            "item": [{"name": "Test Request"}],
            "auth": None
        }
        
        results = self.engine.validate_collection(collection)
        
        # Should have warning about missing collection-level auth
        assert any(r.requirement_id == "coll_002" for r in results)
    
    def test_security_patterns_hardcoded_password(self):
        """Test detection of hardcoded passwords."""
        text = 'password = "secret123"'
        
        results = self.engine.check_security_patterns(text)
        
        assert len(results) > 0
        assert any(r.issue_type == IssueType.SECURITY_VULNERABILITY for r in results)
        assert any(r.severity == Severity.CRITICAL for r in results)
    
    def test_security_patterns_hardcoded_api_key(self):
        """Test detection of hardcoded API keys."""
        text = 'api_key = "abc123xyz"'
        
        results = self.engine.check_security_patterns(text)
        
        assert len(results) > 0
        assert any("API key" in r.issue_description for r in results)
    
    def test_security_patterns_clean_code(self):
        """Test that clean code passes security checks."""
        text = 'username = "testuser"'
        
        results = self.engine.check_security_patterns(text)
        
        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
