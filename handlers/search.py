from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from scraper import AnimeWorldScraper
from config import Config

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🌟 Anime World Bot 🌟\n\n"
        "Send me an anime name to search on anime-world.co"
    )

def handle_search(update: Update, context: CallbackContext):
    query = update.message.text
    results = AnimeWorldScraper.search_anime(query)
    
    if not results:
        update.message.reply_text(f"❌ No results found for '{query}'")
        return
    
    # For simplicity, show first result
    anime = results[0]
    details = AnimeWorldScraper.get_anime_details(anime['link'])
    
    keyboard = [
        [InlineKeyboardButton("📤 Upload to DB", callback_data=f"upload:{anime['link']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"🎬 <b>{details.get('title', anime['title'])}</b>\n\n"
        f"📝 <i>{details.get('description', 'No description available.')[:200]}...</i>\n\n"
        f"🔗 <a href='{anime['link']}'>View on Anime World</a>"
    )
    
    update.message.reply_photo(
        photo=anime['image'],
        caption=message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
