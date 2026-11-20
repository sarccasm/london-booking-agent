from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
import os
from dotenv import load_dotenv

load_dotenv()
LONDON = ZoneInfo('Europe/London')

@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    openai_key: str
    model: str
    manager: str
    live_send: bool
    name: str
    phone: str
    max_messages: int
    base_url: str = 'https://api.openai.com/v1'
    test_mode: bool = False


def load_config() -> Config:
    api_id = os.getenv('TELEGRAM_API_ID', '').strip()
    api_hash = os.getenv('TELEGRAM_API_HASH', '').strip()
    manager = os.getenv('MANAGER_USERNAME', '').strip().lstrip('@')
    test_mode = os.getenv('TEST_MODE', '0') == '1'
    live_send = os.getenv('LIVE_SEND', '0') == '1'
    if not test_mode and (not api_id.isdigit() or not api_hash):
        raise ValueError('Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env')
    if not test_mode and not manager:
        raise ValueError('Set MANAGER_USERNAME in .env')
    provider = os.getenv('AI_PROVIDER', 'omniroute').strip().lower()
    if provider == 'omniroute':
        base_url = os.getenv('AI_BASE_URL', 'http://127.0.0.1:20128/v1').strip()
        key = os.getenv('OMNIROUTE_API_KEY', 'dummy-key').strip() or 'dummy-key'
        model = os.getenv('AI_MODEL', 'auto').strip()
    elif provider == 'openai':
        base_url = 'https://api.openai.com/v1'
        key = os.getenv('OPENAI_API_KEY', '').strip()
        model = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini').strip()
        if not key:
            raise ValueError('OPENAI_API_KEY required when AI_PROVIDER=openai')
    else:
        raise ValueError('AI_PROVIDER must be omniroute or openai')
    return Config(int(api_id) if api_id.isdigit() else 0, api_hash, key,
                  model, manager, live_send, os.getenv('BOOKING_NAME', '').strip(),
                  os.getenv('BOOKING_PHONE', '').strip(),
                  int(os.getenv('MAX_MESSAGES', '12')), base_url, test_mode)


def london_date() -> str:
    return datetime.now(LONDON).date().isoformat()


def london_target_passed() -> bool:
    now = datetime.now(LONDON)
    return (now.hour, now.minute) >= (17, 0)
