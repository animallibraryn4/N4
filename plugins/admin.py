from telegram.ext import CommandHandler, MessageHandler, Filters
from config import Config

def broadcast(update, context):
    """Broadcast a message to all users"""
    user_id = update.message.from_user.id
    
    # Check if user is admin
    if user_id not in Config.ADMINS:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Check if message is a reply
    if not update.message.reply_to_message:
        update.message.reply_text("Please reply to a message to broadcast it.")
        return
    
    message = update.message.reply_to_message
    
    # Here you would add logic to send this message to all users
    # This is a placeholder implementation
    update.message.reply_text("Broadcast functionality would be implemented here.")

def delete_message(update, context):
    """Delete a message"""
    user_id = update.message.from_user.id
    
    # Check if user is admin
    if user_id not in Config.ADMINS:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Check if message is a reply
    if not update.message.reply_to_message:
        update.message.reply_text("Please reply to a message to delete it.")
        return
    
    try:
        context.bot.delete_message(
            chat_id=update.message.reply_to_message.chat_id,
            message_id=update.message.reply_to_message.message_id
        )
        update.message.reply_text("Message deleted successfully.")
    except Exception as e:
        update.message.reply_text(f"Failed to delete message: {str(e)}")

# Command handlers to register
command_handler = [
    ("broadcast", False, broadcast),
    ("delete", False, delete_message)
]
