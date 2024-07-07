import telegram
import os
import asyncio

# load the environment variables
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def send_message(bot_token, chat_id, text):
    bot = telegram.Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=text)


if __name__ == "__main__":
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    text = "Hello, this is a message from your Telegram bot!"

    asyncio.run(send_message(BOT_TOKEN, chat_id, text))
    print("Message sent successfully.")
