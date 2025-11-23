"""
Tests for the validation aggregator.
"""

import pytest
from unittest.mock import Mock, patch
from vigilancepilot.models import APIEndpoint, ValidationResult, Severity, IssueType
from vigilancepilot.detection.aggregator import ValidationAggregator
from vigilancepilot.config import Config


class TestValidationAggregator:
    """Test cases for ValidationAggregator."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=Config)
        config.llm_provider = "openai"
        config.llm_model = "gpt-4-turbo-preview"
        config.openai_api_key = "test-key"
        config.confidence_threshold = 0.75
        return config
    
    @pytest.fixture
    def aggregator(self, mock_config):
        """Create an aggregator instance."""
        with patch('vigilancepilot.detection.aggregator.RulesEngine'), \
             patch('vigilancepilot.detection.aggregator.LLMDetector'):
            return ValidationAggregator(mock_config)
    
    def test_validate_endpoint_rules_only(self, aggregator):
        """Test endpoint validation without LLM."""
        endpoint = APIEndpoint(
            path="/api/v1/users",
            method="GET",
            auth_required=True,
            rate_limited=True
        )
        
        # Mock rule engine results
        mock_result = ValidationResult(
            requirement_id="test_001",
            name="Test Check",
            passed=True,
            confidence=1.0,
            severity=Severity.HIGH
        )
        aggregator.rules_engine.validate_endpoint = Mock(return_value=[mock_result])
        
        results = aggregator.validate_endpoint(endpoint, use_llm=False)
        
        assert len(results) > 0
        assert aggregator.rules_engine.validate_endpoint.called
    
    def test_validate_endpoint_with_llm(self, aggregator):
        """Test endpoint validation with LLM."""
        endpoint = APIEndpoint(
            path="/api/v1/users",
            method="GET",
            auth_required=True,
            rate_limited=True
        )
        
        # Mock both rule engine and LLM detector
        rule_result = ValidationResult(
            requirement_id="rule_001",
            name="Rule Check",
            passed=True,
            confidence=1.0,
            severity=Severity.HIGH
        )
        
        llm_result = ValidationResult(
            requirement_id="llm_001",
            name="LLM Check",
            passed=False,
            confidence=0.85,
            severity=Severity.MEDIUM,
            issue_type=IssueType.OTHER,
            issue_description="Potential issue detected"
        )
        
        aggregator.rules_engine.validate_endpoint = Mock(return_value=[rule_result])
        aggregator.llm_detector.analyze_endpoint = Mock(return_value=[llm_result])
        
        results = aggregator.validate_endpoint(endpoint, use_llm=True)
        
        assert len(results) >= 2
        assert aggregator.llm_detector.analyze_endpoint.called
    
    def test_confidence_threshold_filtering(self, aggregator):
        """Test that results below threshold are filtered out."""
        endpoint = APIEndpoint(
            path="/api/v1/users",
            method="GET",
            auth_required=True,
            rate_limited=True
        )
        
        # Create results with different confidence levels
        results = [
            ValidationResult(
                requirement_id="high_conf",
                name="High Confidence",
                passed=False,
                confidence=0.95,
                severity=Severity.HIGH
            ),
            ValidationResult(
                requirement_id="low_conf",
                name="Low Confidence",
                passed=False,
                confidence=0.5,
                severity=Severity.LOW
            )
        ]
        
        aggregator.rules_engine.validate_endpoint = Mock(return_value=results)
        
        filtered = aggregator.validate_endpoint(endpoint, use_llm=False, threshold=0.75)
        
        # Only high confidence result should remain
        assert len(filtered) == 1
        assert filtered[0].requirement_id == "high_conf"
    
    def test_deduplicate_results(self, aggregator):
        """Test deduplication of validation results."""
        results = [
            ValidationResult(
                requirement_id="dup_001",
                name="Duplicate Check",
                passed=False,
                confidence=0.8,
                severity=Severity.MEDIUM
            ),
            ValidationResult(
                requirement_id="dup_001",
                name="Duplicate Check",
                passed=False,
                confidence=0.9,  # Higher confidence
                severity=Severity.MEDIUM
            )
        ]
        
        deduplicated = aggregator._deduplicate_results(results)
        
        # Should only have one result with higher confidence
        assert len(deduplicated) == 1
        assert deduplicated[0].confidence == 0.9
    
    def test_extract_endpoints_from_collection(self, aggregator):
        """Test endpoint extraction from Postman collection."""
        collection = {
            "item": [
                {
                    "name": "Get Users",
                    "request": {
                        "method": "GET",
                        "url": {"raw": "https://api.example.com/users"},
                        "auth": {"type": "bearer"}
                    }
                },
                {
                    "name": "User Folder",
                    "item": [
                        {
                            "name": "Get User by ID",
                            "request": {
                                "method": "GET",
                                "url": "https://api.example.com/users/123"
                            }
                        }
                    ]
                }
            ]
        }
        
        endpoints = aggregator._extract_endpoints(collection)
        
        assert len(endpoints) == 2
        assert endpoints[0].method == "GET"
        assert endpoints[0].auth_required is True  # Has auth
        assert endpoints[1].path == "https://api.example.com/users/123"
    
    def test_validate_collection(self, aggregator):
        """Test full collection validation."""
        collection = {
            "name": "Test Collection",
            "item": [
                {
                    "name": "Test Request",
                    "request": {
                        "method": "GET",
                        "url": {"raw": "https://api.example.com/test"}
                    }
                }
            ],
            "auth": {"type": "apikey"}
        }
        
        mock_result = ValidationResult(
            requirement_id="coll_001",
            name="Collection Validation",
            passed=True,
            confidence=1.0,
            severity=Severity.MEDIUM
        )
        
        aggregator.rules_engine.validate_collection = Mock(return_value=[mock_result])
        aggregator.rules_engine.validate_endpoint = Mock(return_value=[])
        
        results = aggregator.validate_collection(collection, use_llm=False)
        
        assert len(results) > 0
        assert aggregator.rules_engine.validate_collection.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
