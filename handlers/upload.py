import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from config import Config
from scraper import AnimeWorldScraper

def handle_upload(update: Update, context: CallbackContext):
    if update.effective_user.id not in Config.ADMINS:
        update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    # Implementation for manual upload command
    pass

def upload_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if not query.from_user.id in Config.ADMINS:
        query.edit_message_text("❌ You don't have permission to upload.")
        return
    
    _, anime_url = query.data.split(':')
    details = AnimeWorldScraper.get_anime_details(anime_url)
    
    if not details.get('download_links'):
        query.edit_message_text("❌ No download links found for this anime.")
        return
    
    # Create quality selection keyboard
    keyboard = []
    for quality in Config.ALLOWED_QUALITIES:
        if quality in details['download_links']:
            keyboard.append(
                [InlineKeyboardButton(
                    f"⬇️ Download {quality}",
                    callback_data=f"download:{anime_url}:{quality}"
                )]
            )
    
    if not keyboard:
        query.edit_message_text("❌ No supported quality options available.")
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        "Select quality to download:",
        reply_markup=reply_markup
    )
