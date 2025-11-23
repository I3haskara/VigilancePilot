import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

class Settings:
    AGI_BASE_URL = os.getenv('AGI_BASE_URL', 'https://api.agi.tech/api/v1')
    AGI_API_KEY = os.getenv('AGI_API_KEY', '')
    TELNYX_API_KEY = os.getenv('TELNYX_API_KEY', '')
    TELNYX_PHONE_NUMBER = os.getenv('TELNYX_PHONE_NUMBER', '')
    PARENT_ALERT_PHONE = os.getenv('PARENT_ALERT_PHONE', '')
    TELNYX_WEBHOOK_SECRET = os.getenv('TELNYX_WEBHOOK_SECRET', '')

settings = Settings()
