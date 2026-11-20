import json
from datetime import datetime, timezone
from pathlib import Path

class DecisionLog:
    def __init__(self, directory='logs'):
        Path(directory).mkdir(parents=True, exist_ok=True)
        self.path = Path(directory) / f"decisions-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.jsonl"

    def write(self, *, direction, message, understood='', decision='', status=''):
        record = {'timestamp_utc': datetime.now(timezone.utc).isoformat(),
                  'direction': direction, 'message': message,
                  'understood': understood, 'decision': decision, 'status': status}
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        print(f"[{direction}] {message}\n  understood={understood}; decision={decision}; status={status}")
