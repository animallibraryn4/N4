from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from config import config
from database import Database
import logging
import importlib
import os

# Initialize database
db = Database(config.DB_URI)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f'Error: {context.error}')

def load_plugins(application):
    """Load all plugin handlers"""
    plugins = []
    for filename in os.listdir("plugins"):
        if filename.endswith(".py") and not filename.startswith("__"):
            plugin_name = filename[:-3]
            plugins.append(plugin_name)
            module = importlib.import_module(f"plugins.{plugin_name}")
            
            if hasattr(module, "command_handler"):
                for handler in module.command_handler:
                    if handler[1]:  # Callback handler
                        application.add_handler(CallbackQueryHandler(handler[0], pattern=handler[1]))
                    else:  # Command handler
                        application.add_handler(CommandHandler(handler[0], handler[2] if len(handler) > 2 else handler[0]))
    
    logger.info(f"Loaded plugins: {', '.join(plugins)}")

async def post_init(application: Application) -> None:
    """Set bot commands"""
    await application.bot.set_my_commands([
        ("start", "Start the bot"),
        ("channels", "Manage channels"),
        ("addchannel", "Add new channel")
    ])

def main() -> None:
    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()
    load_plugins(application)
    application.add_error_handler(error_handler)
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
