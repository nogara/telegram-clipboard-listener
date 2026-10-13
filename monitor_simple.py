import pyperclip
import re
import time
import os
import asyncio

# load the environment variables
from dotenv import load_dotenv

load_dotenv()

# create a database to keep already sent messages

from database import UrlDatabaseManager


async def download_video(message):
    # download the video
    command = f'yt-dlp --cookies ./cookies/www.instagram.com_cookies.txt "{message}"'
    os.system(command)

    return "Ok"


async def download_video_twitter(message):
    # download the video
    command = f'yt-dlp --cookies ./cookies/x.com_cookies.txt "{message}"'
    os.system(command)

    return "Ok"


async def download_video_tiktok(message):
    # download the video
    command = f'yt-dlp --cookies ./cookies/tiktok_cookies.txt "{message}"'
    os.system(command)

    return "Ok"


async def amain(loop):
    # Define your pattern here
    # get pattern from the environment variable

    pattern = re.compile(os.environ.get("PATTERN_TO_CHECK"))

    # Store the last copied text to compare with new text
    last_copied_text = ""

    while True:
        # Get the current text from the clipboard
        clipboard_text = pyperclip.paste()

        # check if there is something in the clipboard
        if not clipboard_text:
            time.sleep(1)

        # If the text has changed and matches the pattern
        if clipboard_text != last_copied_text and pattern.search(clipboard_text):
            # check if the text is already sent
            print("New text:", clipboard_text)

            # check if the text is from twitter
            if "x.com" in clipboard_text:
                await download_video_twitter(clipboard_text)
            if "tiktok" in clipboard_text:
                await download_video_tiktok(clipboard_text)
            else:
                await download_video(clipboard_text)
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
