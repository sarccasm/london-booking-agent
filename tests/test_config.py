from datetime import datetime
from zoneinfo import ZoneInfo
from config import LONDON

def test_london_timezone():
    assert datetime(2026, 11, 20, 17, 0, tzinfo=LONDON).utcoffset().total_seconds() == 0
