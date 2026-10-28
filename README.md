# Telegram Bot with Clipboard Monitoring

This project was created with a very specific use case in mind: monitoring the clipboard for specific patterns and sending messages to a Telegram chat. The bot is designed to interact with a specific chat ID and a list of allowed usernames. It can also send messages as a userbot using the Telegram Userbot API.

## Features

- **Clipboard Monitoring:** Monitors the clipboard for specific patterns and can react accordingly.
- **SQLite Database Integration:** Uses a SQLite database (`urls.db`) for storing and managing data efficiently.
- **User-Specific Interaction:** Configured to interact with allowed Telegram usernames and a specific chat ID.
- **Userbot Functionality:** Capable of sending messages as a specific user, utilizing Telegram's Userbot API.

## Configuration

Before running the bot, you need to configure it by creating a `.env` file based on the `.env.example` provided. Fill in the following fields:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
- `ALLOWED_TELEGRAM_USERNAMES`: Usernames allowed to interact with the bot, separated by commas.
- `TELEGRAM_CHAT_ID`: The chat ID where the bot will operate, or the username of the chat.
- `SQLITE_DATABASE`: The path to the SQLite database file.
- `TELEGRAM_USERBOT_API_ID` and `TELEGRAM_USERBOT_API_HASH`: Credentials for using the bot as a userbot.

## Pattern Matching

The bot monitors the clipboard for strings that match a specific pattern. Define this pattern in the `PATTERN_TO_CHECK` variable in your `.env` file.

## Getting Started

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in the necessary details.
3. Install dependencies
4. Run the bot according to the project's run instructions.

## Dependencies

This project uses [Poetry](https://python-poetry.org/) for dependency management. If you don't have Poetry installed, please follow the [official installation instructions](https://python-poetry.org/docs/#installation).

After installing Poetry, you can install the project dependencies by running the following command in the project root directory:

```bash
poetry install
```

This command reads the pyproject.toml file and installs all necessary dependencies in an isolated environment.

## Running the Bot

To run the bot using Poetry, follow these steps:

Activate the Poetry shell by running:

```bash
poetry shell
```

This command activates the virtual environment created by Poetry.

Run the bot script within the activated environment:

```bash
python monitor.py
```

Ensure that you have configured the .env file with all the necessary details before running the bot.
