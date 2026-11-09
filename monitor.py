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
POLL_INTERVAL = 0.3
ALBUM_SIZE = 10
# a TikTok WAF token exported from the browser makes TikTok answer 403 to yt-dlp
# while it is valid (about 5 minutes); yt-dlp gets its own by solving the challenge
BLOCKED_COOKIES = {"_waftokenid"}


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


def strip_cookies(path, names):
    """Removes the named cookies from a Netscape cookies file, if present."""
    with open(path) as f:
        lines = f.readlines()
    kept = [line for line in lines if not set(line.split("\t")[5:6]) & names]
    if len(kept) != len(lines):
        with open(path, "w") as f:
            f.writelines(kept)


async def run_downloader(url, *args):
    """Runs a downloader module from this environment; True if it succeeded."""
    # args are passed as a list so the clipboard content is never
    # interpreted by a shell
    process = await asyncio.create_subprocess_exec(sys.executable, "-m", *args, url)
    try:
        return await asyncio.wait_for(process.wait(), timeout=DOWNLOAD_TIMEOUT) == 0
    except asyncio.TimeoutError:
        process.kill()
        print("Download timed out:", url)
        return False


def downloaded_files(prefix):
    # ignore partial downloads left behind by the downloaders
    return sorted(
        f
        for f in glob.glob(f"{prefix}_*")
        if not f.endswith((".part", ".ytdl")) and ".part-" not in f
    )


async def download_media(url):
    """Downloads the videos and images at url and returns the downloaded files."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    name = hashlib.md5(url.encode()).hexdigest()
    cookies = cookies_for(url)
    strip_cookies(cookies, BLOCKED_COOKIES)

    video_prefix = os.path.join(DOWNLOAD_DIR, f"{name}_v")
    videos_ok = await run_downloader(
        url,
        "yt_dlp",
        "--cookies",
        cookies,
        "--merge-output-format",
        "mp4",
        "-o",
        f"{video_prefix}_%(autonumber)s.%(ext)s",
    )
    videos = downloaded_files(video_prefix)
    if videos_ok and videos:
        return videos

    # yt-dlp only gets videos, so image posts and the images of mixed
    # carousels fail there; gallery-dl gets both, in the post's order
    print("Trying gallery-dl for:", url)
    gallery_prefix = os.path.join(DOWNLOAD_DIR, f"{name}_g")
    await run_downloader(
        url,
        "gallery_dl",
        "--cookies",
        cookies,
        "-D",
        DOWNLOAD_DIR,
        "-f",
        # num is the position in the post; !s keeps a missing num from
        # breaking the format
        f"{name}_g_{{num!s:>03}}_{{filename}}.{{extension}}",
    )
    gallery = downloaded_files(gallery_prefix)
    if gallery:
        remove_files(videos)
        return gallery
    return videos


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


async def send_media(client, files, url):
    entity = await client.get_entity(chat_id())

    # a list of files is sent as an album, which holds at most 10 items
    for i in range(0, len(files), ALBUM_SIZE):
        chunk = files[i : i + ALBUM_SIZE]
        await client.send_file(
            entity,
            chunk if len(chunk) > 1 else chunk[0],
            caption=url,
            supports_streaming=True,
        )
    return "Ok"


async def process_url(client, db, url):
    """Downloads url and sends it to Telegram, marking it as sent on success."""
    print("Downloading:", url)
    files = await download_media(url)
    if not files:
        print("Nothing downloaded for:", url)
        return

    try:
        await send_media(client, files, url)
    except Exception as e:
        # keep the files so they are not lost
        print("Failed to send to Telegram:", e, files)
        return

    # only mark as sent and delete once Telegram has the video
    db.add_record(url)
    remove_files(files)
    print("Sent and removed:", files)


async def worker(name, queue, client, db, in_flight):
    while True:
        url = await queue.get()
        try:
            await process_url(client, db, url)
        except Exception as e:
            print(f"[{name}] Failed to process {url}:", e)
        finally:
            in_flight.discard(url)
            queue.task_done()


async def watch_clipboard(queue, db, pattern, in_flight):
    # Store the last copied text to compare with new text
    last_copied_text = ""

    while True:
        # pbpaste/xclip run as a subprocess, keep it off the event loop
        # paste() returns None when the clipboard holds non-text (e.g. an image)
        clipboard_text = await asyncio.to_thread(pyperclip.paste) or ""

        # If the text has changed and matches the pattern
        if clipboard_text != last_copied_text and pattern.search(clipboard_text):
            last_copied_text = clipboard_text

            if clipboard_text in in_flight:
                print("Already queued:", clipboard_text)
            elif db.check_record_exists(clipboard_text):
                print("Already sent text:", clipboard_text)
            else:
                print("New text:", clipboard_text)
                in_flight.add(clipboard_text)
                queue.put_nowait(clipboard_text)

        await asyncio.sleep(POLL_INTERVAL)


async def amain(loop):
    api_id = os.environ.get("TELEGRAM_USERBOT_API_ID")
    api_hash = os.environ.get("TELEGRAM_USERBOT_API_HASH")

    client = await create_session("session_name", api_id, api_hash)

    # fill Telethon's entity cache so numeric chat ids can be resolved
    await client.get_dialogs()

    # get pattern from the environment variable
    pattern = re.compile(os.environ.get("PATTERN_TO_CHECK"))

    with UrlDatabaseManager("urls.db") as db:
        db.initialize_database()

        # the clipboard is watched on its own while a single worker downloads
        # and sends, so links copied in quick succession are queued instead of
        # missed; downloads run one at a time because yt-dlp rewrites the
        # shared cookies file on exit and parallel runs read it half-written
        queue = asyncio.Queue()
        in_flight = set()
        download_worker = asyncio.create_task(
            worker("worker", queue, client, db, in_flight)
        )
        try:
            await watch_clipboard(queue, db, pattern, in_flight)
        finally:
            download_worker.cancel()


if __name__ == "__main__":

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(amain(loop=loop))
    except KeyboardInterrupt:
        pass
