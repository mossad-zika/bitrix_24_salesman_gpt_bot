from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


# returns an instance of a builder class, which has the methods .token() and .build(). These methods are designed to
# return the builder instance itself after performing some operations, allowing you to chain method calls together.
application = Application.builder().token("TOKEN").build()
