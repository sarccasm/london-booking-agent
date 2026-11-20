"""Run a local rehearsal or a real Telegram booking conversation."""
import asyncio
from telethon import TelegramClient, events
from config import load_config, london_date, london_target_passed
from agent import BookingAgent
from logger import DecisionLog


async def run_local_test(cfg, log, agent):
    opening = agent.opening()
    print('\n=== LOCAL TEST; NO TELEGRAM MESSAGES ===')
    print('AGENT:', opening.message)
    log.write(direction='outbound_test', message=opening.message,
              understood=opening.understood, decision=opening.decision, status=opening.status)
    count = 1
    while count < cfg.max_messages:
        try:
            manager_text = (await asyncio.to_thread(input, '\nMANAGER (/quit to exit): ')).strip()
        except (EOFError, KeyboardInterrupt):
            return
        if manager_text.lower() == '/quit':
            return
        if not manager_text:
            continue
        log.write(direction='inbound_test', message=manager_text,
                  understood='Simulated manager response', decision='Evaluate response', status='received')
        try:
            decision = await agent.respond(manager_text)
        except Exception as exc:
            log.write(direction='error', message=str(exc), understood='AI request failed',
                      decision='Stop safely', status='needs_user')
            print('ERROR:', exc)
            return
        log.write(direction='outbound_test' if decision.status in {'continue', 'confirmed'} else 'system',
                  message=decision.message, understood=decision.understood,
                  decision=decision.decision, status=decision.status)
        print(f'AGENT [{decision.status}]: {decision.message}')
        print('REASON:', decision.decision)
        count += 1
        if decision.status != 'continue':
            print('Local test ended:', decision.status, '(NOT a real booking)')
            return


async def run_telegram(cfg, log, agent):
    client = TelegramClient('booking_agent_session', cfg.api_id, cfg.api_hash)
    await client.start()
    try:
        me = await client.get_me()
        peer = await client.get_entity(cfg.manager)
        if peer.id == me.id:
            raise ValueError('Cannot use own Telegram account as manager. Use TEST_MODE=1.')
        print('Target:', cfg.manager, '| Live send:', cfg.live_send)
        opening = agent.opening()
        if not cfg.live_send:
            log.write(direction='dry_run', message=opening.message,
                      understood=opening.understood, decision='No send: LIVE_SEND=0', status='continue')
            print('DRY RUN, no message sent:', opening.message)
            return
        finished = asyncio.Event()
        count = 0
        lock = asyncio.Lock()

        @client.on(events.NewMessage(chats=peer, incoming=True))
        async def on_message(event):
            nonlocal count
            async with lock:
                if finished.is_set():
                    return
                text = (event.raw_text or '').strip()
                log.write(direction='inbound', message=text,
                          understood='Manager reply received', decision='Assess reply', status='received')
                if not text or count >= cfg.max_messages:
                    log.write(direction='system', message='', understood='Media or message limit',
                              decision='Stop safely', status='needs_user')
                    finished.set()
                    return
                try:
                    result = await agent.respond(text)
                    # If the agent needs information only the operator knows,
                    # pause and ask in the local terminal, then retry safely.
                    attempts = 0
                    while result.status == 'needs_user' and attempts < 2:
                        question = result.message or result.decision or 'What information is missing?'
                        print('\\nAGENT NEEDS YOUR INPUT:', question, flush=True)
                        answer = (await asyncio.to_thread(input, 'YOUR ANSWER (/stop to cancel): ')).strip()
                        if not answer or answer.lower() == '/stop':
                            log.write(direction='system', message='',
                                      understood='Operator did not provide information',
                                      decision='Stop without inventing details', status='needs_user')
                            finished.set()
                            return
                        # Save only the operator's explicit answer, never guess.
                        agent.user_notes.append({'question': question, 'answer': answer})
                        log.write(direction='operator', message='[operator supplied information]',
                                  understood=question, decision='Retry with operator facts', status='received')
                        # respond() already stored the last manager message.
                        # Remove it before retrying to avoid duplicate turns.
                        if agent.history and agent.history[-1] == {'role': 'user', 'content': text}:
                            agent.history.pop()
                        result = await agent.respond(text)
                        attempts += 1
                    if result.status in {'continue', 'confirmed'}:
                        if not result.message:
                            raise ValueError('Empty outgoing message')
                        await client.send_message(peer, result.message)
                        count += 1
                        log.write(direction='outbound', message=result.message,
                                  understood=result.understood, decision=result.decision, status=result.status)
                    else:
                        log.write(direction='system', message=result.message,
                                  understood=result.understood, decision=result.decision, status=result.status)
                    if result.status != 'continue':
                        finished.set()
                except Exception as exc:
                    print("REAL ERROR:", repr(exc))
                    log.write(direction='error', message=str(exc), understood='Send or AI failed',
                              decision='Stop safely', status='needs_user')
                    finished.set()

        await client.send_message(peer, opening.message)
        count = 1
        log.write(direction='outbound', message=opening.message,
                  understood=opening.understood, decision=opening.decision, status=opening.status)
        print('Opening sent; waiting for manager reply.')
        try:
            await asyncio.wait_for(finished.wait(), timeout=1800)
        except asyncio.TimeoutError:
            log.write(direction='system', message='', understood='No reply within 30 minutes',
                      decision='Stop without confirmation', status='timeout')
    finally:
        await client.disconnect()


async def main():
    cfg = load_config()
    date = london_date()
    agent = BookingAgent(cfg.openai_key, cfg.model, date, cfg.name, cfg.phone, cfg.base_url)
    log = DecisionLog()
    print(f'London date: {date} | AI: {cfg.base_url} | model: {cfg.model} | test: {cfg.test_mode}')
    if cfg.test_mode:
        await run_local_test(cfg, log, agent)
    else:
        await run_telegram(cfg, log, agent)


if __name__ == '__main__':
    asyncio.run(main())
