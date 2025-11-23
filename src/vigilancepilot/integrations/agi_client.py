"""
AGI Agent API client for browser-based AI agents.
Handles session management and agent interactions.
"""

from typing import Dict, Any, List, Optional
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time


class AGIClient:
    """
    Client for interacting with AGI Agent API.
    Enables browser-based AI agents that can navigate and interact with the web.
    """
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        Initialize AGI Agent API client.
        
        Args:
            api_key: AGI Agent API key
            base_url: Base URL for AGI Agent API (defaults to AGI_BASE_URL env var)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.base_url = base_url or os.getenv("AGI_BASE_URL", "https://api.agi.tech/api/v1")
        self.timeout = timeout
        self.session = self._create_session(max_retries)
    
    def _create_session(self, max_retries: int) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
        return session
    
    def create_session(self, agent_name: str = "agi-0") -> Dict[str, Any]:
        """
        Create a new browser session with an AI agent.
        
        Args:
            agent_name: Name of the agent to use (e.g., "agi-0")
            
        Returns:
            Session data including session_id
        """
        url = f"{self.base_url}/sessions"
        
        payload = {
            "agent_name": agent_name
        }
        
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        
        return response.json()
    
    def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Send a message/instruction to an agent session.
        
        Args:
            session_id: The session ID
            message: Natural language instruction for the agent
            
        Returns:
            Response data from the API
        """
        url = f"{self.base_url}/sessions/{session_id}/message"
        
        payload = {
            "message": message
        }
        
        response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        
        return response.json()
    
    def get_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the status of an agent session.
        
        Args:
            session_id: The session ID
            
        Returns:
            Status data including current state
        """
        url = f"{self.base_url}/sessions/{session_id}/status"
        
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        return response.json()
    
    def get_messages(self, session_id: str) -> Dict[str, Any]:
        """
        Get messages from an agent session.
        
        Args:
            session_id: The session ID
            
        Returns:
            Messages data including agent responses
        """
        url = f"{self.base_url}/sessions/{session_id}/messages"
        
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        return response.json()
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Delete/cleanup an agent session.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            Deletion confirmation
        """
        url = f"{self.base_url}/sessions/{session_id}"
        
        response = self.session.delete(url, timeout=self.timeout)
        response.raise_for_status()
        
        return response.json()
    
    def wait_for_completion(
        self, 
        session_id: str, 
        poll_interval: int = 2, 
        max_wait: int = 300,
        status_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Wait for an agent session to complete.
        
        Args:
            session_id: The session ID
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait
            status_callback: Optional callback function(status_dict) called on each poll
            
        Returns:
            Final status dictionary
            
        Raises:
            TimeoutError: If max_wait is exceeded
        """
        start_time = time.time()
        
        while True:
            status = self.get_status(session_id)
            
            if status_callback:
                status_callback(status)
            
            if status.get("status") in ["finished", "error"]:
                return status
            
            elapsed = time.time() - start_time
            if elapsed >= max_wait:
                raise TimeoutError(f"Session {session_id} did not complete within {max_wait} seconds")
            
            time.sleep(poll_interval)
    
    def extract_final_results(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Extract final results from a completed session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of result messages
        """
        messages = self.get_messages(session_id)
        
        # Filter for final results (e.g., DONE messages)
        results = []
        for msg in messages.get("messages", []):
            if msg.get("type") == "DONE":
                results.append(msg)
        
        return results
    
    def run_task(
        self, 
        task: str, 
        agent_name: str = "agi-0",
        wait: bool = True,
        poll_interval: int = 2,
        max_wait: int = 300
    ) -> Dict[str, Any]:
        """
        Convenience method to run a complete task: create session, send message, wait, get results.
        
        Args:
            task: Natural language task description
            agent_name: Agent to use
            wait: Whether to wait for completion
            poll_interval: Seconds between status checks (if wait=True)
            max_wait: Maximum seconds to wait (if wait=True)
            
        Returns:
            Complete task result including session_id, status, and results
        """
        # Create session
        session_data = self.create_session(agent_name=agent_name)
        session_id = session_data.get("session_id")
        
        try:
            # Send task
            self.send_message(session_id, task)
            
            if wait:
                # Wait for completion
                status = self.wait_for_completion(
                    session_id, 
                    poll_interval=poll_interval,
                    max_wait=max_wait
                )
                
                # Get final results
                results = self.extract_final_results(session_id)
                
                return {
                    "session_id": session_id,
                    "status": status,
                    "results": results
                }
            else:
                return {
                    "session_id": session_id,
                    "status": self.get_status(session_id)
                }
        finally:
            # Cleanup session if needed (or leave it for manual cleanup)
            pass


