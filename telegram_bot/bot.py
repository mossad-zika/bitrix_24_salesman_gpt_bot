#!/usr/bin/env python

import asyncio
import base64
from io import BytesIO
import logging
import os
from openai import OpenAI
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set a higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Set your OpenAI API key
# Replace None with your OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate an image based on a prompt and send it back to the user as an image."""
    if not context.args:
        await update.message.reply_text("Please provide a description for the image after the /image command.")
        return

    prompt = ' '.join(context.args)

    # This function will be used to keep sending the typing action
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
                model="dall-e-3",
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
        else:
            await update.message.reply_text("Sorry, the image generation did not succeed.")

    except Exception as e:
        keep_upload_photo.is_upload_photo = False
        await typing_task

        logging.error(f"Error generating image: {e}")
        await update.message.reply_text("Sorry, there was an error generating your image.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def gpt_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a soviet comrade helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        # Access text content from "message" within the first "Choice"
        ai_response = response.choices[0].message.content
        await update.message.reply_text(ai_response.strip(), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        await update.message.reply_text("Sorry, I couldn't process your message at the moment.")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    application = Application.builder().token(telegram_bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("image", image_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_prompt))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
