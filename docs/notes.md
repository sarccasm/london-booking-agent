# Tool choices and AI use (draft, edit to match actual work)

1. Considered n8n, but its Telegram Bot API workflow cannot initiate a DM to an arbitrary user.
2. Selected Python and Telethon to initiate and receive messages via an authorized Telegram user account.
3. Selected OpenAI API to interpret free-form replies and draft polite British-English responses.
4. Used Python's zoneinfo to resolve today's date and 17:00 in Europe/London.
5. Used python-dotenv for local configuration, keeping secrets outside source control.
6. Used JSONL for a timestamped, machine-readable per-message decision log.
7. Added guardrails for missing restaurant identity, missing personal details, and alternate times.
8. Used AI assistance to scaffold code, review conversation logic, and prepare tests and documentation.
9. Planned second-account testing before contacting the actual manager.
