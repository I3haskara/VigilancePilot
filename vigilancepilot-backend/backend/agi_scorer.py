"""
AGI Scorer Integration Module
Handles AI-powered API response validation and scoring using Claude/OpenAI
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import anthropic
import openai

from models import (
    APITestRequest,
    APITestResponse,
    ValidationResult,
    AGIScoreRequest,
    AGIScoreResponse,
    ScoreBreakdown,
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AGIScorer:
    """AGI-powered API testing and validation scoring system"""
    
    def __init__(self):
        """Initialize AGI Scorer with API clients"""
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.default_provider = os.getenv("AGI_PROVIDER", "anthropic")
        
        self.anthropic_client: Optional[anthropic.AsyncAnthropic] = None
        self.openai_client: Optional[openai.AsyncOpenAI] = None
        
        self.history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
    async def initialize(self):
        """Initialize API clients"""
        try:
            if self.anthropic_api_key:
                self.anthropic_client = anthropic.AsyncAnthropic(
                    api_key=self.anthropic_api_key
                )
                logger.info("Anthropic client initialized")
            
            if self.openai_api_key:
                self.openai_client = openai.AsyncOpenAI(
                    api_key=self.openai_api_key
                )
                logger.info("OpenAI client initialized")
            
            if not self.anthropic_client and not self.openai_client:
                logger.warning("No AGI API keys configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize AGI clients: {str(e)}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.anthropic_client:
            await self.anthropic_client.close()
        if self.openai_client:
            await self.openai_client.close()
    
    async def check_health(self) -> bool:
        """Check if AGI services are available"""
        return bool(self.anthropic_client or self.openai_client)
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        try:
            message = await self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API call failed: {str(e)}")
            raise
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4096
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    async def _call_agi(self, prompt: str) -> str:
        """Call configured AGI provider"""
        if self.default_provider == "anthropic" and self.anthropic_client:
            return await self._call_anthropic(prompt)
        elif self.default_provider == "openai" and self.openai_client:
            return await self._call_openai(prompt)
        elif self.anthropic_client:
            return await self._call_anthropic(prompt)
        elif self.openai_client:
            return await self._call_openai(prompt)
        else:
            raise ValueError("No AGI provider available")
    
    async def test_and_validate(
        self,
        url: str,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        expected_status: int = 200,
        validation_rules: Optional[List[str]] = None
    ) -> APITestResponse:
        """
        Test API endpoint and validate response with AGI
        
        Args:
            url: API endpoint URL
            method: HTTP method
            headers: Request headers
            body: Request body
            expected_status: Expected status code
            validation_rules: Custom validation rules
        
        Returns:
            APITestResponse with validation results
        """
        import httpx
        
        start_time = datetime.utcnow()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Execute API request
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers or {},
                    json=body
                )
                
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Parse response
                try:
                    response_data = response.json()
                except:
                    response_data = {"raw": response.text}
                
                # Build AGI validation prompt
                prompt = self._build_validation_prompt(
                    url=url,
                    method=method,
                    status_code=response.status_code,
                    expected_status=expected_status,
                    response_data=response_data,
                    validation_rules=validation_rules
                )
                
                # Get AGI analysis
                agi_analysis = await self._call_agi(prompt)
                
                # Parse AGI response
                validation_result = self._parse_agi_validation(agi_analysis)
                
                # Create response
                test_response = APITestResponse(
                    success=response.status_code == expected_status,
                    status_code=response.status_code,
                    response_data=response_data,
                    response_time=response_time,
                    validation=validation_result,
                    timestamp=start_time.isoformat()
                )
                
                # Store in history
                self._add_to_history(test_response.dict())
                
                return test_response
                
        except Exception as e:
            logger.error(f"API test failed: {str(e)}")
            return APITestResponse(
                success=False,
                status_code=0,
                response_data={"error": str(e)},
                response_time=0,
                validation=ValidationResult(
                    is_valid=False,
                    errors=[f"Request failed: {str(e)}"],
                    warnings=[],
                    agi_score=0,
                    agi_feedback="API request failed"
                ),
                timestamp=start_time.isoformat()
            )
    
    def _build_validation_prompt(
        self,
        url: str,
        method: str,
        status_code: int,
        expected_status: int,
        response_data: Dict[str, Any],
        validation_rules: Optional[List[str]] = None
    ) -> str:
        """Build AGI validation prompt"""
        prompt = f"""Analyze this API response and provide validation feedback.

API Endpoint: {method} {url}
Expected Status: {expected_status}
Actual Status: {status_code}

Response Data:
{json.dumps(response_data, indent=2)}

Validation Rules:
{json.dumps(validation_rules or [], indent=2)}

Please provide:
1. Overall validation score (0-100)
2. List of errors found
3. List of warnings or improvements
4. Detailed feedback on response quality
5. Recommendations for improvement

Format your response as JSON:
{{
    "score": <0-100>,
    "errors": [<list of errors>],
    "warnings": [<list of warnings>],
    "feedback": "<detailed feedback>",
    "recommendations": [<list of recommendations>]
}}
"""
        return prompt
    
    def _parse_agi_validation(self, agi_response: str) -> ValidationResult:
        """Parse AGI validation response"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', agi_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(agi_response)
            
            return ValidationResult(
                is_valid=data.get("score", 0) >= 70,
                errors=data.get("errors", []),
                warnings=data.get("warnings", []),
                agi_score=data.get("score", 0),
                agi_feedback=data.get("feedback", ""),
                recommendations=data.get("recommendations", [])
            )
        except Exception as e:
            logger.error(f"Failed to parse AGI response: {str(e)}")
            return ValidationResult(
                is_valid=False,
                errors=["Failed to parse AGI validation"],
                warnings=[],
                agi_score=0,
                agi_feedback=agi_response[:500]
            )
    
    async def score_response(
        self,
        endpoint: str,
        response_data: Dict[str, Any],
        expected_schema: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> AGIScoreResponse:
        """Score an API response using AGI"""
        prompt = f"""Score this API response on multiple dimensions.

Endpoint: {endpoint}
Context: {context or "N/A"}

Response Data:
{json.dumps(response_data, indent=2)}

Expected Schema:
{json.dumps(expected_schema or {}, indent=2)}

Please score (0-100) on these dimensions:
1. Correctness: Does the response match expectations?
2. Completeness: Is all required data present?
3. Performance: Response structure efficiency
4. Security: Any security concerns?
5. Usability: API usability and clarity

Format as JSON:
{{
    "overall_score": <0-100>,
    "breakdown": {{
        "correctness": <0-100>,
        "completeness": <0-100>,
        "performance": <0-100>,
        "security": <0-100>,
        "usability": <0-100>
    }},
    "feedback": "<detailed feedback>",
    "recommendations": [<list>]
}}
"""
        
        try:
            agi_response = await self._call_agi(prompt)
            data = json.loads(agi_response)
            
            return AGIScoreResponse(
                endpoint=endpoint,
                overall_score=data.get("overall_score", 0),
                breakdown=ScoreBreakdown(**data.get("breakdown", {})),
                feedback=data.get("feedback", ""),
                recommendations=data.get("recommendations", []),
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.error(f"Scoring failed: {str(e)}")
            raise
    
    async def batch_validate(
        self,
        requests: List[APITestRequest]
    ) -> List[APITestResponse]:
        """Validate multiple API endpoints"""
        tasks = [
            self.test_and_validate(
                url=req.url,
                method=req.method,
                headers=req.headers,
                body=req.body,
                expected_status=req.expected_status,
                validation_rules=req.validation_rules
            )
            for req in requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        validated_results = []
        for result in results:
            if isinstance(result, Exception):
                validated_results.append(
                    APITestResponse(
                        success=False,
                        status_code=0,
                        response_data={"error": str(result)},
                        response_time=0,
                        validation=ValidationResult(
                            is_valid=False,
                            errors=[str(result)],
                            warnings=[],
                            agi_score=0,
                            agi_feedback="Batch validation failed"
                        ),
                        timestamp=datetime.utcnow().isoformat()
                    )
                )
            else:
                validated_results.append(result)
        
        return validated_results
    
    def _add_to_history(self, result: Dict[str, Any]):
        """Add result to history"""
        self.history.append(result)
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    async def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get test history"""
        return self.history[-limit:]
    
    async def clear_history(self):
        """Clear test history"""
        self.history.clear()
