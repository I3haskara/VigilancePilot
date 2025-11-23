"""
LLM-powered detector for deeper API validation reasoning.
"""

from typing import List, Dict, Any, Optional
import json

from vigilancepilot.models import ValidationResult, Severity, IssueType, APIEndpoint
from vigilancepilot.config import Config


class LLMDetector:
    """
    Uses LLM to perform deeper reasoning about API specifications,
    test coverage, and potential issues that rule-based checks might miss.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the LLM detector.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.provider = config.llm_provider
        self.model = config.llm_model
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client."""
        if self.provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=self.config.openai_api_key)
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            return Anthropic(api_key=self.config.anthropic_api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def analyze_endpoint(self, endpoint: APIEndpoint, context: Optional[str] = None) -> List[ValidationResult]:
        """
        Analyze an API endpoint using LLM for deeper insights.
        
        Args:
            endpoint: The API endpoint to analyze
            context: Optional additional context
            
        Returns:
            List of validation results from LLM analysis
        """
        prompt = self._build_endpoint_analysis_prompt(endpoint, context)
        response = self._call_llm(prompt)
        return self._parse_llm_response(response)
    
    def analyze_test_coverage(self, collection: Dict[str, Any], endpoints: List[APIEndpoint]) -> List[ValidationResult]:
        """
        Analyze test coverage for a collection of endpoints.
        
        Args:
            collection: Postman collection data
            endpoints: List of API endpoints
            
        Returns:
            List of validation results for test coverage
        """
        prompt = self._build_coverage_analysis_prompt(collection, endpoints)
        response = self._call_llm(prompt)
        return self._parse_llm_response(response)
    
    def _build_endpoint_analysis_prompt(self, endpoint: APIEndpoint, context: Optional[str]) -> str:
        """Build prompt for endpoint analysis."""
        endpoint_json = endpoint.model_dump_json(indent=2)
        
        prompt = f"""Analyze the following API endpoint for potential issues, security vulnerabilities, 
and best practice violations. Consider authentication, authorization, input validation, 
error handling, and security implications.

Endpoint specification:
{endpoint_json}

{f"Additional context: {context}" if context else ""}

Provide your analysis as a JSON array of issues, where each issue has:
- requirement_id: unique identifier
- name: short name of the check
- passed: boolean (false if issue found)
- confidence: 0.0-1.0 confidence score
- severity: "low", "medium", "high", or "critical"
- issue_type: one of {[t.value for t in IssueType]}
- issue_description: detailed description
- recommendations: array of actionable recommendations

Focus on issues that rule-based systems might miss, such as:
- Logical security flaws
- Business logic vulnerabilities
- Unusual patterns that could indicate problems
- Missing best practices
- Potential data leakage

Return ONLY the JSON array, no other text."""
        
        return prompt
    
    def _build_coverage_analysis_prompt(self, collection: Dict[str, Any], endpoints: List[APIEndpoint]) -> str:
        """Build prompt for test coverage analysis."""
        collection_name = collection.get("name", "Unknown")
        num_tests = len(collection.get("item", []))
        num_endpoints = len(endpoints)
        
        prompt = f"""Analyze test coverage for the following API collection:

Collection: {collection_name}
Number of test cases: {num_tests}
Number of endpoints: {num_endpoints}

Endpoints summary:
{json.dumps([{"method": e.method, "path": e.path} for e in endpoints], indent=2)}

Evaluate:
1. Are all endpoints covered by tests?
2. Are edge cases tested (error conditions, boundary values)?
3. Are security scenarios tested (unauthorized access, injection attacks)?
4. Are different authentication states tested?
5. Is the testing comprehensive enough?

Provide your analysis as a JSON array of issues following the same format as before.
Focus on gaps in test coverage and missing test scenarios.

Return ONLY the JSON array, no other text."""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM with the given prompt.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            LLM response text
        """
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert API security and testing analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.3,
                    system="You are an expert API security and testing analyst.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
            
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {str(e)}")
    
    def _parse_llm_response(self, response: str) -> List[ValidationResult]:
        """
        Parse LLM response into ValidationResult objects.
        
        Args:
            response: Raw LLM response
            
        Returns:
            List of ValidationResult objects
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            
            issues = json.loads(json_str)
            
            results = []
            for issue in issues:
                results.append(ValidationResult(
                    requirement_id=issue.get("requirement_id", "llm_unknown"),
                    name=issue.get("name", "LLM Analysis"),
                    passed=issue.get("passed", True),
                    confidence=issue.get("confidence", 0.7),
                    severity=issue.get("severity", "medium"),
                    issue_type=issue.get("issue_type"),
                    issue_description=issue.get("issue_description"),
                    recommendations=issue.get("recommendations", [])
                ))
            
            return results
            
        except json.JSONDecodeError as e:
            # If parsing fails, return a single result indicating the issue
            return [ValidationResult(
                requirement_id="llm_parse_error",
                name="LLM Analysis Parse Error",
                passed=False,
                confidence=0.5,
                severity=Severity.LOW,
                issue_type=IssueType.OTHER,
                issue_description=f"Failed to parse LLM response: {str(e)}",
                recommendations=["Review LLM output manually"]
            )]
