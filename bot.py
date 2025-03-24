from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# To this:
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler
from telegram.ext.filters import TEXT, PHOTO, DOCUMENT  # Add specific filters you need
from config import Config
import logging
import importlib
import os
from plugins import *

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def load_plugins():
    """Dynamically load all plugins from the plugins directory"""
    plugins = []
    for filename in os.listdir("plugins"):
        if filename.endswith(".py") and not filename.startswith("__"):
            plugin_name = filename[:-3]
            plugins.append(plugin_name)
            
            # Import the plugin
            module = importlib.import_module(f"plugins.{plugin_name}")
            
            # Register handlers if they exist
            if hasattr(module, "command_handler"):
                for handler in module.command_handler:
                    if handler[1]:  # If it's a callback handler
                        dispatcher.add_handler(CallbackQueryHandler(handler[0], pattern=handler[1]))
                    else:  # Regular command handler
                        dispatcher.add_handler(CommandHandler(handler[0], handler[2] if len(handler) > 2 else handler[0]))
    
    logger.info(f"Loaded plugins: {', '.join(plugins)}")

def main():
    """Start the bot"""
    updater = Updater(Config.BOT_TOKEN, use_context=True)
    global dispatcher
    dispatcher = updater.dispatcher
    
    # Load all plugins
    load_plugins()
    
    # Start the Bot
    updater.start_polling()
    logger.info("Bot started and running...")
    updater.idle()

if __name__ == '__main__':
    main()
