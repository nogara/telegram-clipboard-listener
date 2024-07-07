from telegram import Bot
import os

# load the environment variables
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.environ.get("TELEGRAM_CHANNEL_USERNAME")


def get_channel_id(bot_token, channel_username):
    bot = Bot(token=bot_token)
    chat = bot.get_chat(chat_id=channel_username)
    return chat.id


if __name__ == "__main__":
    channel_id = get_channel_id(BOT_TOKEN, CHANNEL_USERNAME)
    print(f"Channel ID: {channel_id}")
