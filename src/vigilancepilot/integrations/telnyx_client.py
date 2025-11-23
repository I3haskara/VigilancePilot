"""
Telnyx SMS client for sending alerts and notifications.
"""

from typing import Optional
import requests


class TelnyxClient:
    """
    Client for sending SMS alerts via Telnyx.
    """
    
    BASE_URL = "https://api.telnyx.com/v2"
    
    def __init__(self, api_key: str, from_number: str):
        """
        Initialize Telnyx client.
        
        Args:
            api_key: Telnyx API key
            from_number: Sender phone number (E.164 format)
        """
        self.api_key = api_key
        self.from_number = from_number
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with auth headers."""
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        return session
    
    def send_sms(self, to_number: str, message: str) -> dict:
        """
        Send an SMS message.
        
        Args:
            to_number: Recipient phone number (E.164 format)
            message: Message text
            
        Returns:
            Response data from Telnyx API
        """
        url = f"{self.BASE_URL}/messages"
        
        payload = {
            "from": self.from_number,
            "to": to_number,
            "text": message
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def send_validation_alert(
        self, 
        to_number: str, 
        collection_name: str,
        failed_checks: int,
        total_checks: int,
        severity: str = "high"
    ):
        """
        Send a validation alert via SMS.
        
        Args:
            to_number: Recipient phone number
            collection_name: Name of the collection
            failed_checks: Number of failed checks
            total_checks: Total number of checks
            severity: Severity level
        """
        emoji = "🚨" if severity in ["high", "critical"] else "⚠️"
        
        message = (
            f"{emoji} VigilancePilot Alert\n\n"
            f"Collection: {collection_name}\n"
            f"Failed: {failed_checks}/{total_checks}\n"
            f"Severity: {severity.upper()}\n\n"
            f"Check your dashboard for details."
        )
        
        return self.send_sms(to_number, message)
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate a phone number format.
        
        Args:
            phone_number: Phone number to validate
            
        Returns:
            True if valid E.164 format
        """
        import re
        # Simple E.164 validation
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone_number))
