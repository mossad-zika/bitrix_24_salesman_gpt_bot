from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Though methods themselves aren’t typically considered attributes,
    # attributes can reference callable objects,
    # including methods from other objects.
    # This can sometimes lead to confusion
    # but is a powerful feature in Python.
    await update.message.reply_text("Shalom World!")


application = Application.builder().token("TOKEN").build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
application.run_polling(allowed_updates=Update.ALL_TYPES)
