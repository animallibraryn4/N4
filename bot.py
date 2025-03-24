from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
import logging
import importlib
import os
from plugins import *

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f'Update {update} caused error {context.error}')

def load_plugins(application):
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
                        application.add_handler(CallbackQueryHandler(handler[0], pattern=handler[1]))
                    else:  # Regular command handler
                        if len(handler) > 2:
                            application.add_handler(CommandHandler(handler[0], handler[2]))
                        else:
                            application.add_handler(CommandHandler(handler[0], handler[0]))
    
    logger.info(f"Loaded plugins: {', '.join(plugins)}")

async def post_init(application: Application) -> None:
    """Post initialization tasks."""
    await application.bot.set_my_commands([
        ("start", "Start the bot"),
        ("help", "Get help")
    ])

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(Config.BOT_TOKEN).post_init(post_init).build()
    
    # Load all plugins
    load_plugins(application)
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Run the bot until Ctrl-C is pressed
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
