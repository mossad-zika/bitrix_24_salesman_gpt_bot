#!/usr/bin/env python

import asyncio
import base64
from io import BytesIO
import logging
import os
import re

from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from logfmter import Logfmter
import asyncpg

# Enable logging
formatter = Logfmter(
    keys=["at", "logger", "level", "msg"],
    mapping={"at": "asctime", "logger": "name", "level": "levelname", "msg": "message"},
    datefmt='%H:%M:%S %d/%m/%Y'
)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
file_handler = logging.FileHandler("./logs/bot.log")
file_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[stream_handler, file_handler]
)
# set a higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Set your OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Global variables
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-3.5-turbo")
DALL_E_MODEL = os.getenv("DALL_E_MODEL", "dall-e-3")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful assistant.")


async def db_connect():
    return await asyncpg.connect(user=os.getenv("POSTGRES_USER"),
                                 password=os.getenv("POSTGRES_PASSWORD"),
                                 database=os.getenv("POSTGRES_DB"),
                                 port=os.getenv("POSTGRES_PORT"),
                                 host=os.getenv("DB_HOST"))


async def is_user_allowed(user_id: int) -> bool:
    conn = await db_connect()
    try:
        existing_user = await conn.fetchval("SELECT user_id FROM allowed_users WHERE user_id = $1",
                                            user_id)
        return existing_user is not None
    finally:
        await conn.close()


def split_into_chunks(text, chunk_size):
    """
    Split text into chunks of specified size.
    """
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


def escape_markdown(text: str) -> str:
    """Helper function to escape telegram markup symbols."""

    escape_chars = r"\_*[]()~>#+-=|{}.!"

    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Shalom {user.mention_html()}!",
    )


async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate an image based on a prompt and send it back to the user as an image."""
    user = update.effective_user

    if not context.args:
        logger.error(f"User {user.id} ({user.username}) did not provide a prompt for the /image command.")
        await update.message.reply_text("Please provide a description for the image after the /image command.",
                                        reply_to_message_id=update.message.message_id)
        return

    prompt = ' '.join(context.args)
    logging.info(f"User {user.id} ({user.username}) requested an image with prompt: '{prompt}'")

    if not await is_user_allowed(user.id):
        logger.info("User %s (%s) tried to generate an image but is not allowed.", user.id, user.username)
        await update.message.reply_text("Sorry, you are not allowed to generate images.",
                                        reply_to_message_id=update.message.message_id)
        return

    async def keep_upload_photo():
        while keep_upload_photo.is_upload_photo:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='upload_photo')
            await asyncio.sleep(1)

    keep_upload_photo.is_upload_photo = True

    typing_task = asyncio.create_task(keep_upload_photo())

    try:
        response = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: client.images.generate(
                model=DALL_E_MODEL,
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json"
            )
        )

        keep_upload_photo.is_upload_photo = False
        await typing_task

        if hasattr(response, 'data') and len(response.data) > 0:
            await update.message.reply_photo(photo=BytesIO(base64.b64decode(response.data[0].b64_json)))
            logging.info(f"Successfully generated an image for prompt: '{prompt}'")
        else:
            await update.message.reply_text("Sorry, the image generation did not succeed.",
                                            reply_to_message_id=update.message.message_id)
            logging.error(f"Failed to generate image for prompt: '{prompt}'")

    except Exception as e:
        keep_upload_photo.is_upload_photo = False
        await typing_task

        logger.error(f"Error generating image: {e}")
        logging.error(f"Error generating image for prompt: '{prompt}': {e}")
        await update.message.reply_text("Sorry, there was an error generating your image.",
                                        reply_to_message_id=update.message.message_id)


async def gpt_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a response to the user's text message using GPT."""
    user_message = update.message.text
    user = update.effective_user
    logging.info(f"User {user.id} ({user.username}) requested sent text: '{user_message}'")

    if not await is_user_allowed(user.id):
        logger.info("User %s (%s) tried to use GPT prompt but is not allowed.", user.id, user.username)
        await update.message.reply_text("Sorry, you are not allowed to text with me.",
                                        reply_to_message_id=update.message.message_id)
        return

    async def keep_typing():
        while keep_typing.is_typing:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            await asyncio.sleep(1)

    keep_typing.is_typing = True

    typing_task = asyncio.create_task(keep_typing())

    try:
        response = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ]
            )
        )

        keep_typing.is_typing = False

        ai_response = escape_markdown(response.choices[0].message.content)
        logging.info(f"Response for user {user.id} ({user.username}): '{ai_response.strip()}'")
        ai_response_chunks = split_into_chunks(ai_response.strip(), 4096)
        for chunk in ai_response_chunks:
            await update.message.reply_text(chunk,
                                            reply_to_message_id=update.message.message_id,
                                            parse_mode="MarkdownV2")

    except Exception as e:
        keep_typing.is_typing = False
        logger.error("Error generating AI response: %s", e)
        await update.message.reply_text("Sorry, I couldn't process your message at the moment.",
                                        reply_to_message_id=update.message.message_id)

    await typing_task


def main() -> None:
    """Start the bot."""
    logger.info("Starting the bot...")
    logger.info("GPT Model: %s", GPT_MODEL)
    logger.info("DALL-E Model: %s", DALL_E_MODEL)
    logger.info("System Prompt: %s", SYSTEM_PROMPT)
    # Create the Application and pass it your bot's token.
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    application = Application.builder().token(telegram_bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("image", generate_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_prompt))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
