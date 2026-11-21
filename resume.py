"""One-off continuation of an existing Telegram conversation; never sends a new opening."""
import asyncio
from telethon import TelegramClient
from config import load_config, london_date
from agent import BookingAgent
from logger import DecisionLog


async def main():
    cfg = load_config()
    log = DecisionLog()
    client = TelegramClient('booking_agent_session', cfg.api_id, cfg.api_hash)
    await client.start()
    try:
        peer = await client.get_entity(cfg.manager)
        messages = list(reversed(await client.get_messages(peer, limit=15)))
        inbound = [m for m in messages if not m.out and (m.raw_text or '').strip()]
        if not inbound:
            print('No incoming manager messages found. Nothing sent.')
            return
        # Safety: this continuation is only for the existing unavailable-17:00 case.
        # Reconstruct history without sending another booking request.
        agent = BookingAgent(cfg.openai_key, cfg.model, london_date(),
                             cfg.name, cfg.phone, cfg.base_url)
        for m in messages:
            text = (m.raw_text or '').strip()
            if text:
                agent.history.append({
                    'role': 'assistant' if m.out else 'user',
                    'content': text,
                })
        # The most recent incoming message may be just "Hello?".
        # Provide the full conversation to the AI, not just the last message.
        latest = inbound[-1]
        if any(m.out and m.id > latest.id for m in messages):
            print('A newer outgoing reply already exists. Nothing sent.')
            return
        # Remove latest manager turn because respond() adds it itself.
        for i in range(len(agent.history)-1, -1, -1):
            if agent.history[i]['role'] == 'user' and agent.history[i]['content'] == latest.raw_text.strip():
                del agent.history[i]
                break
        decision = await agent.respond(latest.raw_text.strip())
        print('AI status:', decision.status)
        print('Proposed reply:', decision.message)
        log.write(direction='resume_proposal', message=decision.message,
                  understood=decision.understood, decision=decision.decision,
                  status=decision.status)
        if decision.status not in {'declined', 'continue'} or not decision.message:
            print('No safe outgoing response. Nothing sent.')
            return
        # Explicitly require the operator to approve this one message.
        if not cfg.live_send:
            print('DRY RUN: LIVE_SEND=0. Nothing sent.')
            return
        confirmation = (await asyncio.to_thread(
            input, 'Send exactly this one reply to the manager? Type SEND: '
        )).strip()
        if confirmation != 'SEND':
            print('Cancelled. Nothing sent.')
            return
        # Recheck in case another reply arrived while the operator was deciding.
        latest_now = (await client.get_messages(peer, limit=1))[0]
        if latest_now.id != messages[-1].id:
            print('Conversation changed. Nothing sent; review new messages.')
            return
        await client.send_message(peer, decision.message)
        log.write(direction='outbound', message=decision.message,
                  understood=decision.understood, decision=decision.decision,
                  status=decision.status)
        print('One reply sent. Done.')
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
