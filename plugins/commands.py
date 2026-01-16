from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from config import config
from loguru import logger

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        if update.effective_chat.type != "private":
            await update.message.reply_text("Please use this command in private chat.")
            return
        
        args = context.args
        if args:
            file_hash = args[0].split("_")[-1]
            
            # Get file from database
            from database import db
            doc = await db.get_file_by_hash(file_hash)
            
            if not doc:
                await update.message.reply_text("❌ File not found or link expired.")
                return
            
            # Forward the file
            await context.bot.forward_message(
                chat_id=update.effective_chat.id,
                from_chat_id=config.FILES_CHANNEL,
                message_id=doc['message_id'],
                protect_content=True
            )
            
            logger.info(f"File sent to {update.effective_user.id}")
        else:
            # Show help message
            await update.message.reply_text(
                "👋 Hello! I'm AutoAnimeBot\n\n"
                "I automatically download and upload anime from SubsPlease RSS feed.\n\n"
                "Join our channel: @AutoAnimeChannel"
            )
    
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

async def alive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alive command (owner only)"""
    user_id = update.effective_user.id
    if user_id not in config.OWNER_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    await update.message.reply_text("✅ Bot is alive and running!")
    logger.info(f"Alive command executed by {user_id}")

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /logs command (owner only)"""
    user_id = update.effective_user.id
    if user_id not in config.OWNER_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    try:
        # Send log file
        with open(config.LOG_FILE, 'rb') as log_file:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=log_file,
                filename="bot.log",
                caption="📊 Bot logs"
            )
        
        logger.info(f"Logs sent to {user_id}")
    
    except Exception as e:
        logger.error(f"Error sending logs: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command (owner only)"""
    user_id = update.effective_user.id
    if user_id not in config.OWNER_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    try:
        from database import db
        
        # Get status info
        remaining = await db.get_remaining_anime()
        is_working = await db.is_worker_busy()
        
        status_text = (
            "🤖 **Bot Status**\n"
            "──────────────\n"
            f"• **Worker Status:** {'🟢 Working' if is_working else '🟡 Idle'}\n"
            f"• **Queue Length:** {len(remaining)} anime\n"
            f"• **Database:** {'🟢 Connected'}\n"
            "──────────────\n"
            "Use /logs to get detailed logs."
        )
        
        await update.message.reply_text(status_text, parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

async def manual_check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual check for new anime (owner only)"""
    user_id = update.effective_user.id
    if user_id not in config.OWNER_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    try:
        from plugins.anime_handler import AnimeHandler
        anime_handler = AnimeHandler(context.bot, context.bot, db)
        
        await update.message.reply_text("🔄 Checking for new anime...")
        await anime_handler.check_new_anime()
        await update.message.reply_text("✅ Check completed!")
    
    except Exception as e:
        logger.error(f"Error in manual check: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

async def setup_commands(application, anime_handler=None):
    """Setup all command handlers"""
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("alive", alive_command))
    application.add_handler(CommandHandler("logs", logs_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("check", manual_check_command))
    
    logger.info("Command handlers setup completed")
