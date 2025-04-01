from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from config import Config
from handlers import (
    channel_handler,
    post_handler,
    settings_handler,
    admin_handler
)
from database.database import SessionLocal

def main():
    updater = Updater(Config.TOKEN)
    dp = updater.dispatcher
    
    # Add handlers
    dp.add_handler(CommandHandler("start", admin_handler.start))
    dp.add_handler(CallbackQueryHandler(channel_handler.add_channel, pattern="^add_channel$"))
    dp.add_handler(CallbackQueryHandler(post_handler.create_post, pattern="^create_post$"))
    
    # Message handlers
    dp.add_handler(MessageHandler(
        Filters.forwarded & Filters.chat_type.channel,
        lambda u, c: channel_handler.handle_channel_forward(u, c, SessionLocal())
    ))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
