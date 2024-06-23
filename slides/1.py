from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

application = Application.builder().token("TOKEN").build()

# Creating an instance (also called an object) of the CommandHandler class,
# and then passing that instance to the
# add_handler method of application.
# Pass to the constructor the command name and the function
# that should be executed when the command is received.
application.add_handler(CommandHandler("start", start))

# so-called "shortcuts" to filtering messages methods.
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# In Object-Oriented Programming (OOP), an attribute is a variable that belongs to a class.
application.run_polling(allowed_updates=Update.ALL_TYPES)
