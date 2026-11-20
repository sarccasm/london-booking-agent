# London Restaurant Booking Agent (AI Builder test)

Custom-built autonomous Telegram user-client agent using **Python, Telethon, OpenAI API**. It initiates a polite English booking request for **two people at 17:00 today in London**, handles replies, and records one JSONL log entry per incoming/outgoing message. It never invents a restaurant name or confirmation.

> IMPORTANT: This is a real messaging agent, **not** the previous n8n DEMO booking workflow. Never contact the assessment manager before testing with your own second Telegram account.

## Setup (Windows PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` from https://my.telegram.org, and `OPENAI_API_KEY` from your API account. Set `MANAGER_USERNAME` to **your second Telegram account** first. `LIVE_SEND=0` prevents sending. Telegram will request login code on first start. Never commit `.env` or `*.session` files.

```powershell
python main.py
```

To run an actual test, set `LIVE_SEND=1` **only with your own second account**. Send replies from the second account and inspect `logs/decisions-*.jsonl`. Then switch `MANAGER_USERNAME=vlad_dev_7` only when ready for the real attempt.

## Safety / behaviour

- Agent stops if 17:00 has already passed in London. This avoids promising an impossible future booking. If the deadline has passed, discuss rescheduling rather than silently altering the requirement.
- Does not accept alternate times without authorization.
- Does not invent restaurant name, personal name or phone number. Supply `BOOKING_NAME` and `BOOKING_PHONE` only if you choose to share them. Missing details cause safe stop (`needs_user`).
- An explicit manager confirmation must mention confirmation, 17:00 and two people. Restaurant name must be explicitly supplied by manager (e.g. `The restaurant name is Example Bistro`). Otherwise the agent asks for clarification or stops. Conservative checks may require operator intervention.
- Voice messages are not supported in the baseline (optional stretch task).
- Telegram may restrict messages from a user account to someone who has not contacted it; do not attempt to bypass platform limits.
- Do not run multiple copies or use a shared session file concurrently.
- Decision logs are local and may contain personal data. Do not publish raw logs without review/redaction.

## GitHub

```powershell
git init
git add .
git commit -m "Build Telegram restaurant booking agent"
git branch -M main
gh repo create london-booking-agent --private --source . --push
```

If `gh` is unavailable, create an empty repository on GitHub and follow its push instructions. Share a reviewed repo link with the recruiter; ensure they can access a private repo if used.

## Deliverables

1. Screenshot full Telegram conversation (after actual manager interaction).
2. GitHub repository link.
3. `logs/decisions-*.jsonl`, reviewed and redacted as necessary.
4. `docs/notes.md` (tools and AI use).
5. `docs/limitations.md` (honest account of failures and uncertainty).

## Test scenarios

Second account replies: `We have a table for two at 5 pm. The restaurant name is Example Bistro. Your reservation is confirmed for 2 people at 17:00.` Check whether the final message repeats all facts. Also test a refusal, a counteroffer for 17:30, a missing restaurant name, a request for phone number, and no reply.

## Known limitations

The AI can misunderstand unusual phrasing. Automatic verification is deliberately conservative and may stop without confirming a genuine booking. The code has not been authenticated against your Telegram account or tested against the actual manager; only a local syntax/test check has been performed. The user's account must have permission to message the manager.
