import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from handlers import search, upload, admin
from config import Config

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    updater = Updater(Config.TOKEN)
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler("start", search.start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, search.handle_search))
    dp.add_handler(CommandHandler("upload", upload.handle_upload))
    dp.add_handler(CommandHandler("admin", admin.admin_panel))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
