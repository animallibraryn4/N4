import os
import json
import requests
import threading
from telegram import Update, InputMediaVideo
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
QUALITY = os.getenv("DEFAULT_QUALITY", "720p")

# Load anime sources
with open('config.json') as f:
    SOURCES = json.load(f)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🎌 Anime Auto-Download Bot\n\n"
        "Available Commands:\n"
        "/download <anime> <quality>\n"
        "/list - Show available anime\n"
        "/setquality <480p|720p|1080p>\n\n"
        "Example: /download solo-leveling 720p"
    )

def list_anime(update: Update, context: CallbackContext):
    anime_list = "\n".join([f"• {anime}" for anime in SOURCES.keys()])
    update.message.reply_text(f"Available Anime:\n{anime_list}")

def download_and_upload(anime, quality, update, context):
    try:
        if anime in SOURCES and quality in SOURCES[anime]:
            update.message.reply_text(f"⬇️ Downloading {anime} in {quality}...")
            
            # Simulate download (replace with actual download logic)
            for episode, url in SOURCES[anime][quality].items():
                # Download would happen here
                # For now we'll simulate with the URL
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Downloaded: {episode} ({quality})"
                )
                
                # Upload to channel
                context.bot.send_video(
                    chat_id=CHANNEL_ID,
                    video=url,  # In real use, this would be the file
                    caption=f"{anime.replace('-', ' ').title()} {episode} [{quality}]"
                )
                
            update.message.reply_text("✅ All episodes uploaded to your channel!")
        else:
            update.message.reply_text("❌ Invalid anime or quality")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")

def download_command(update: Update, context: CallbackContext):
    try:
        args = context.args
        if len(args) < 1:
            update.message.reply_text("Usage: /download <anime> [quality]")
            return
            
        anime = args[0].lower()
        quality = args[1].lower() if len(args) > 1 else QUALITY
        
        # Start download in separate thread
        threading.Thread(
            target=download_and_upload,
            args=(anime, quality, update, context)
        ).start()
        
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("list", list_anime))
    dp.add_handler(CommandHandler("download", download_command))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
