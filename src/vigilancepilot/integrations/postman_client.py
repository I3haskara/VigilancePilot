"""
Postman API client for fetching collections and running tests.
"""

from typing import Dict, Any, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class PostmanClient:
    """
    Client for interacting with Postman API.
    Supports fetching collections, environments, and running tests.
    """
    
    BASE_URL = "https://api.postman.com"
    
    def __init__(self, api_key: str, timeout: int = 30, max_retries: int = 3):
        """
        Initialize Postman client.
        
        Args:
            api_key: Postman API key
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.timeout = timeout
        self.session = self._create_session(max_retries)
    
    def _create_session(self, max_retries: int) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        })
        
        return session
    
    def get_collection(self, collection_id: str) -> Dict[str, Any]:
        """
        Fetch a Postman collection by ID.
        
        Args:
            collection_id: The collection ID
            
        Returns:
            Collection data
        """
        url = f"{self.BASE_URL}/collections/{collection_id}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        return data.get("collection", {})
    
    def list_collections(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all collections.
        
        Args:
            workspace_id: Optional workspace ID to filter by
            
        Returns:
            List of collection metadata
        """
        url = f"{self.BASE_URL}/collections"
        params = {}
        
        if workspace_id:
            params["workspace"] = workspace_id
        
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        return data.get("collections", [])
    
    def get_environment(self, environment_id: str) -> Dict[str, Any]:
        """
        Fetch a Postman environment by ID.
        
        Args:
            environment_id: The environment ID
            
        Returns:
            Environment data
        """
        url = f"{self.BASE_URL}/environments/{environment_id}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        return data.get("environment", {})
    
    def create_collection_run(
        self, 
        collection_id: str, 
        environment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a collection run (trigger test execution).
        
        Note: This requires a monitor or Newman integration.
        For now, this is a placeholder for future implementation.
        
        Args:
            collection_id: The collection ID
            environment_id: Optional environment ID
            
        Returns:
            Run metadata
        """
        # Note: Direct collection runs require Postman monitors or Newman
        # This is a simplified implementation
        raise NotImplementedError(
            "Collection runs require Postman Monitor or Newman integration. "
            "Use Newman CLI or Postman Cloud Agent for execution."
        )
    
    def get_collection_requests(self, collection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all requests from a collection.
        
        Args:
            collection: Collection data
            
        Returns:
            List of request objects
        """
        requests_list = []
        
        def extract_requests(items: List[Dict[str, Any]]):
            """Recursively extract requests from items."""
            for item in items:
                if "request" in item:
                    requests_list.append(item)
                if "item" in item:
                    extract_requests(item["item"])
        
        extract_requests(collection.get("item", []))
        return requests_list
    
    def validate_api_key(self) -> bool:
        """
        Validate the API key by making a test request.
        
        Returns:
            True if API key is valid
        """
        try:
            url = f"{self.BASE_URL}/me"
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException:
            return False
