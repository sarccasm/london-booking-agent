# London Booking Agent

AI Builder take-home task: an independent Telegram user-client agent that starts a conversation in British English and attempts to reserve a restaurant table for **two people at 17:00 London time**.

## Demonstration

Tested end-to-end on **20 November 2026** using two Telegram accounts controlled by the developer. The agent started the conversation, handled the manager's reply, requested explicit confirmation and the restaurant name, received confirmation for **The Garden Bistro**, and sent a final confirmation message. This was **a simulation**, not a real restaurant booking or a conversation with the assessment manager.

## Tech stack

- Python and Telethon for Telegram user-account messaging
- Google Gemini via local OmniRoute (OpenAI-compatible HTTP endpoint)
- `openai` Python SDK as an API client
- `python-dotenv` for configuration, `zoneinfo` for Europe/London time
- JSONL decision logs for inbound/outbound messages and agent decisions

## Local setup

1. Install Python dependencies: `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env`. Set Telegram API credentials from https://my.telegram.org and configure `MANAGER_USERNAME` to your **own second test account**.
3. Start OmniRoute in a separate terminal: `npx omniroute`. Configure a supported Gemini provider/model in the OmniRoute dashboard. Keep the process running.
4. Set `AI_PROVIDER=omniroute`, `AI_BASE_URL=http://127.0.0.1:20128/v1`, and a model available in your OmniRoute instance (the demo used `gemini/gemini-3.1-flash-lite`).
5. Run `python main.py`. With `TEST_MODE=1`, replies are entered in the terminal. With `TEST_MODE=0` and `LIVE_SEND=0`, Telegram connectivity is checked without sending.
6. Use `LIVE_SEND=1` **only** when intentionally messaging a controlled test account or a manager who is ready to receive the request. Starting the program again sends a new opening message.

Do not commit `.env`, `*.session` or private logs.

## Behaviour

The agent initiates the request, interprets manager replies, requests the restaurant name when missing, and requires an explicit confirmation before reporting success. It does not intentionally accept alternative times. Ambiguous responses can lead to a safe stop. The voice-message stretch goal was not implemented.

**Important limitation:** the time-expiration guard was disabled locally for the after-17:00 demonstration; the checked-in version should not be treated as a production-ready booking system. Restore/strengthen that guard before actual live reservations.

## Deliverables

- Telegram conversation screenshot (test accounts): see the screenshot supplied with the submission; it is not stored in this repository
- [Transcribed demonstration conversation](docs/demo-transcript.md)
- Source code in this repository
- Decision-log evidence: local `logs/decisions-*.jsonl` files are ignored for privacy; share a reviewed/redacted export separately if required
- [Tool choices and AI use](docs/notes.md)
- [Difficulties and limitations](docs/limitations.md)

The repository is private; grant the evaluator access or change visibility only if appropriate.
