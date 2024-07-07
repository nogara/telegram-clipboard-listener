import os
import asyncio
from telethon import TelegramClient
# load the environment variables
from dotenv import load_dotenv

load_dotenv()

async def create_session(session_name, api_id, api_hash):
    client = TelegramClient("session_name", api_id, api_hash)
    await client.start()
    return client

async def send_message(client):
    entity = await client.get_entity(os.environ.get("TELEGRAM_CHAT_ID"))
    await client.send_message(entity, "Hello! Talking to you from Telethon")
    return "Ok"

async def amain(loop):
    api_id = os.environ.get("TELEGRAM_USERBOT_API_ID")
    api_hash = os.environ.get("TELEGRAM_USERBOT_API_HASH")

    client = await create_session("session_name", api_id, api_hash)

    await send_message(client)

    print("Ok.")


if __name__ == "__main__":

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(amain(loop=loop))
    except KeyboardInterrupt:
        pass
