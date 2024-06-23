from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


# Define a command handler. These usually take the two-argument update and context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text("Shalom World!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


# Create the Application and pass it your bot's token.
application = Application.builder().token("TOKEN").build()

# on different commands - answer in Telegram
application.add_handler(CommandHandler("start", start))

# on non command i.e., message - echo the message on Telegram
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Run the bot until the user presses Ctrl-C
application.run_polling(allowed_updates=Update.ALL_TYPES)
