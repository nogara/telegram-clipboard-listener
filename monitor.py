import pyperclip
import re
import time
import os
import asyncio
from telethon import TelegramClient

# load the environment variables
from dotenv import load_dotenv

load_dotenv()

# create a database to keep already sent messages

from database import UrlDatabaseManager

async def create_session(session_name, api_id, api_hash):
    client = TelegramClient("session_name", api_id, api_hash)
    await client.start()
    return client


async def send_message(client, message):
    entity = await client.get_entity(os.environ.get("TELEGRAM_CHAT_ID"))

    await client.send_message(entity, message)
    return "Ok"


async def amain(loop):
    api_id = os.environ.get("TELEGRAM_USERBOT_API_ID")
    api_hash = os.environ.get("TELEGRAM_USERBOT_API_HASH")

    client = await create_session("session_name", api_id, api_hash)

    # Define your pattern here
    # get pattern from the environment variable

    pattern = re.compile(os.environ.get("PATTERN_TO_CHECK"))

    with UrlDatabaseManager("urls.db") as db:
        db.initialize_database()

        # Store the last copied text to compare with new text
        last_copied_text = ""

        while True:
            # Get the current text from the clipboard
            clipboard_text = pyperclip.paste()

            # If the text has changed and matches the pattern
            if clipboard_text != last_copied_text and pattern.search(clipboard_text):
                # check if the text is already sent
                if db.check_record_exists(clipboard_text):
                    print("Already sent text:", clipboard_text)
                    last_copied_text = clipboard_text
                    continue
                else:
                    db.add_record(clipboard_text)
                    print("New text:", clipboard_text)
                    await send_message(client, clipboard_text)
                last_copied_text = clipboard_text

            # Wait for a second before checking again
            time.sleep(1)


if __name__ == "__main__":

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(amain(loop=loop))
    except KeyboardInterrupt:
        pass

