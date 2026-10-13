import pyperclip
import re
import os
import sys
import glob
import hashlib
import asyncio
from telethon import TelegramClient

# load the environment variables
from dotenv import load_dotenv

load_dotenv()

# create a database to keep already sent messages

from database import UrlDatabaseManager

DOWNLOAD_DIR = "downloads"
DOWNLOAD_TIMEOUT = 300


async def create_session(session_name, api_id, api_hash):
    client = TelegramClient("session_name", api_id, api_hash)
    await client.start()
    return client


def cookies_for(url):
    if "x.com" in url or "twitter.com" in url:
        return "./cookies/x.com_cookies.txt"
    if "tiktok" in url:
        return "./cookies/tiktok_cookies.txt"
    return "./cookies/www.instagram.com_cookies.txt"


async def download_video(url):
    """Downloads the video(s) at url and returns the list of downloaded files."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    prefix = os.path.join(DOWNLOAD_DIR, hashlib.md5(url.encode()).hexdigest())

    # run yt-dlp from the same environment, passing args as a list so the
    # clipboard content is never interpreted by a shell
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "yt_dlp",
        "--cookies",
        cookies_for(url),
        "--merge-output-format",
        "mp4",
        "-o",
        f"{prefix}_%(autonumber)s.%(ext)s",
        url,
    )
    try:
        await asyncio.wait_for(process.wait(), timeout=DOWNLOAD_TIMEOUT)
    except asyncio.TimeoutError:
        process.kill()
        print("Download timed out:", url)

    # ignore partial downloads left behind by yt-dlp
    return sorted(
        f
        for f in glob.glob(f"{prefix}_*")
        if not f.endswith((".part", ".ytdl")) and ".part-" not in f
    )


def remove_files(files):
    for f in files:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass


def chat_id():
    # numeric ids come from the env as strings, but Telethon only resolves
    # them as ids when they are ints; usernames like "@foo" or "me" stay as is
    value = os.environ.get("TELEGRAM_CHAT_ID")
    try:
        return int(value)
    except ValueError:
        return value


async def send_video(client, files, url):
    entity = await client.get_entity(chat_id())

    # a list of files is sent as an album, with the caption on the first one
    await client.send_file(
        entity,
        files if len(files) > 1 else files[0],
        caption=url,
        supports_streaming=True,
    )
    return "Ok"


async def amain(loop):
    api_id = os.environ.get("TELEGRAM_USERBOT_API_ID")
    api_hash = os.environ.get("TELEGRAM_USERBOT_API_HASH")

    client = await create_session("session_name", api_id, api_hash)

    # fill Telethon's entity cache so numeric chat ids can be resolved
    await client.get_dialogs()

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
                last_copied_text = clipboard_text

                # check if the text is already sent
                if db.check_record_exists(clipboard_text):
                    print("Already sent text:", clipboard_text)
                    continue

                print("New text:", clipboard_text)
                files = await download_video(clipboard_text)
                if not files:
                    print("Nothing downloaded for:", clipboard_text)
                    continue

                try:
                    await send_video(client, files, clipboard_text)
                except Exception as e:
                    # keep the files so they are not lost
                    print("Failed to send to Telegram:", e, files)
                    continue

                # only mark as sent and delete once Telegram has the video
                db.add_record(clipboard_text)
                remove_files(files)
                print("Sent and removed:", files)

            # Wait for a second before checking again
            await asyncio.sleep(1)


if __name__ == "__main__":

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(amain(loop=loop))
    except KeyboardInterrupt:
        pass
