# Tools and AI use

1. Built a custom Python booking agent instead of using a ready-made restaurant booking bot.
2. Used **Telethon** to send and receive messages from a Telegram user account, including starting the conversation.
3. Used **Google Gemini** through the local **OmniRoute** proxy to interpret free-form manager replies and compose short, polite British-English messages.
4. Used the **OpenAI-compatible Python SDK** to call OmniRoute; this does not mean that OpenAI models powered the successful demonstration.
5. Used `zoneinfo` for the London date/time and `python-dotenv` for local configuration.
6. Logged message direction, text, what the agent understood, its decision, and status using JSONL.
7. Added explicit booking confirmation checks, restaurant-name extraction, and refusal of alternative times.
8. Used AI assistance to develop/debug the code, improve prompts, and devise scenarios.
9. Tested locally first, then completed a real Telegram message exchange between two developer-controlled accounts on **20 November 2026**. The booking itself was simulated.
