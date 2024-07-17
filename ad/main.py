# main.py

import logging_setup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import TOKEN
from bot_handlers import start, get_username, verify_code, reset_password, button_callback

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d'), get_username))
    application.add_handler(MessageHandler(filters.Regex(r'^unlock ') & filters.TEXT, verify_code))
    application.add_handler(MessageHandler(filters.Regex(r'^reset ') & filters.TEXT, reset_password))

    logging_setup.logger.info("Bot is starting...") 

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
