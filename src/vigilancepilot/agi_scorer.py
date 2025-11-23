import os
import httpx
from dotenv import load_dotenv
load_dotenv()

AGI_API_KEY = os.getenv("AGI_API_KEY")
AGI_ASSISTANT_ID = os.getenv("AGI_ASSISTANT_ID")

class AGIScorer:
    """
    Handles sending text to AGI.tech, receiving analysis,
    and normalizing the output into a structured risk result.
    """

    def __init__(self) -> None:
        if not AGI_API_KEY:
            raise ValueError("Missing AGI_API_KEY in environment variables")

        if not AGI_ASSISTANT_ID:
            raise ValueError("Missing AGI_ASSISTANT_ID in environment variables")

        self.base_url = "https://api.agi.tech/v1"

    async def analyze_text(self, text: str) -> dict:
        """
        Sends the message to AGI.tech and retrieves structured analysis.
        """
        url = f"{self.base_url}/assistants/{AGI_ASSISTANT_ID}/messages"

        headers = {
            "Authorization": f"Bearer {AGI_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "messages": [{"role": "user", "content": text}],
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)

        resp.raise_for_status()
        raw = resp.json()
        return self._normalize_response(raw)

    def _normalize_response(self, raw: dict) -> dict:
        """
        Convert AGI output into our standardized result format.
        """
        try:
            content = raw["messages"][0]["content"]
        except Exception:
            content = "Could not extract content"

        return {
            "agi_raw": raw,
            "agi_summary": content,
            "risk_score": self._compute_risk(content),
        }

    def _compute_risk(self, text: str) -> int:
        """
        Converts AGI summary into a simple threat score (0–100).
        """
        text = text.lower()

        high_risk_terms = ["grooming", "sexual", "meet up", "secret", "don't tell"]
        medium_terms = ["alone", "private", "location"]

        score = 0

        if any(t in text for t in high_risk_terms):
            score += 70
        if any(t in text for t in medium_terms):
            score += 30

        return min(score, 100)
