from telegram.ext import CommandHandler
from config import Config
import time
from database import get_last_restart

def restart(update, context):
    """Handle the /restart command"""
    user_id = update.message.from_user.id
    
    # Check if user is admin
    if user_id not in Config.ADMINS:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Check cooldown
    last_restart = get_last_restart()
    current_time = time.time()
    
    if last_restart and (current_time - last_restart) < Config.RESTART_COOLDOWN:
        update.message.reply_text(f"Please wait {int(Config.RESTART_COOLDOWN - (current_time - last_restart))} seconds before restarting again.")
        return
    
    # Perform restart
    update.message.reply_text("Restarting server...")
    
    # Save restart time to database
    save_last_restart(current_time)
    
    # Here you would add your actual restart logic
    # For a real implementation, you might need to use system commands or an API

# Command handlers to register
command_handler = [
    ("restart", False, restart)
]
