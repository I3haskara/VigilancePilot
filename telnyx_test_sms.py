import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TELNYX_API_KEY")
FROM = os.getenv("TELNYX_FROM_NUMBER")
TO = os.getenv("TELNYX_TO_NUMBER")
PROFILE_ID = os.getenv("TELNYX_MESSAGING_PROFILE_ID")
print(f"DEBUG TELNYX_API_KEY: {API_KEY!r}")

async def main():
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            "https://api.telnyx.com/v2/messages",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "from": FROM,
                "to": TO,
                "text": "VigilancePilot test SMS from direct script.",
                "messaging_profile_id": PROFILE_ID,
            },
        )
    print(resp.status_code, resp.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
