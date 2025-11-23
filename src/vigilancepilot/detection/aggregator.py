"""
Aggregator that combines rule-based and LLM-based validation results.
"""

from typing import List, Dict, Any, Optional

from vigilancepilot.models import ValidationResult, APIEndpoint
from vigilancepilot.detection.rules_engine import RulesEngine
from vigilancepilot.detection.llm_detector import LLMDetector
from vigilancepilot.config import Config


class ValidationAggregator:
    """
    Combines results from rule-based checks and LLM analysis
    to provide comprehensive validation.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the validation aggregator.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.rules_engine = RulesEngine(config=config.__dict__)
        self.llm_detector = LLMDetector(config=config)
    
    def validate_endpoint(
        self, 
        endpoint: APIEndpoint, 
        use_llm: bool = True,
        threshold: float = 0.75
    ) -> List[ValidationResult]:
        """
        Validate an endpoint using both rule-based and LLM checks.
        
        Args:
            endpoint: The API endpoint to validate
            use_llm: Whether to use LLM analysis
            threshold: Confidence threshold for filtering results
            
        Returns:
            Aggregated list of validation results
        """
        results = []
        
        # Run rule-based checks
        rule_results = self.rules_engine.validate_endpoint(endpoint)
        results.extend(rule_results)
        
        # Run LLM analysis if enabled
        if use_llm:
            try:
                llm_results = self.llm_detector.analyze_endpoint(endpoint)
                results.extend(llm_results)
            except Exception as e:
                # If LLM fails, log but continue with rule-based results
                print(f"LLM analysis failed: {e}")
        
        # Filter by confidence threshold
        filtered_results = [r for r in results if r.confidence >= threshold]
        
        # Deduplicate and merge similar results
        return self._deduplicate_results(filtered_results)
    
    def validate_collection(
        self,
        collection: Dict[str, Any],
        use_llm: bool = True,
        threshold: float = 0.75
    ) -> List[ValidationResult]:
        """
        Validate a Postman collection.
        
        Args:
            collection: Postman collection data
            use_llm: Whether to use LLM analysis
            threshold: Confidence threshold
            
        Returns:
            Aggregated validation results
        """
        results = []
        
        # Validate collection structure
        collection_results = self.rules_engine.validate_collection(collection)
        results.extend(collection_results)
        
        # Extract endpoints from collection items
        endpoints = self._extract_endpoints(collection)
        
        # Validate each endpoint
        for endpoint in endpoints:
            endpoint_results = self.validate_endpoint(
                endpoint, 
                use_llm=use_llm, 
                threshold=threshold
            )
            results.extend(endpoint_results)
        
        # Run collection-level LLM analysis if enabled
        if use_llm and endpoints:
            try:
                coverage_results = self.llm_detector.analyze_test_coverage(
                    collection, 
                    endpoints
                )
                results.extend(coverage_results)
            except Exception as e:
                print(f"LLM coverage analysis failed: {e}")
        
        return self._deduplicate_results(results)
    
    def _extract_endpoints(self, collection: Dict[str, Any]) -> List[APIEndpoint]:
        """
        Extract API endpoints from a Postman collection.
        
        Args:
            collection: Postman collection data
            
        Returns:
            List of APIEndpoint objects
        """
        endpoints = []
        
        def process_item(item: Dict[str, Any]):
            """Recursively process collection items."""
            if "request" in item:
                # This is a request item
                request = item["request"]
                url = request.get("url", {})
                
                if isinstance(url, dict):
                    path = url.get("raw", "")
                elif isinstance(url, str):
                    path = url
                else:
                    path = ""
                
                # Extract auth from request or use collection auth
                auth = request.get("auth")
                auth_required = auth is not None or collection.get("auth") is not None
                
                endpoint = APIEndpoint(
                    path=path,
                    method=request.get("method", "GET"),
                    description=item.get("name"),
                    auth_required=auth_required,
                    rate_limited=False,  # Can't determine from Postman collection
                    tags=[]
                )
                endpoints.append(endpoint)
            
            # Process nested items (folders)
            if "item" in item:
                for nested_item in item["item"]:
                    process_item(nested_item)
        
        # Process all items in collection
        for item in collection.get("item", []):
            process_item(item)
        
        return endpoints
    
    def _deduplicate_results(self, results: List[ValidationResult]) -> List[ValidationResult]:
        """
        Deduplicate and merge similar validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Deduplicated list
        """
        seen = {}
        deduplicated = []
        
        for result in results:
            # Use requirement_id + name as key
            key = f"{result.requirement_id}:{result.name}"
            
            if key not in seen:
                seen[key] = result
                deduplicated.append(result)
            else:
                # Merge with existing result (keep higher confidence)
                existing = seen[key]
                if result.confidence > existing.confidence:
                    # Replace with higher confidence result
                    deduplicated.remove(existing)
                    deduplicated.append(result)
                    seen[key] = result
        
        # Sort by severity (critical first) then confidence
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        deduplicated.sort(
            key=lambda r: (severity_order.get(r.severity.value, 4), -r.confidence)
        )
        
        return deduplicated
