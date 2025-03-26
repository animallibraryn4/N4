import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import requests
from bs4 import BeautifulSoup

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your bot token
TOKEN = "7632805578:AAHyFiomSTFhIxt56vHnosOREPg2iMU8_TQ"
BASE_URL = "https://anime-world.co/category/anime/"

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! Send me an anime name to search on anime-world.co')

def search_anime(update: Update, context: CallbackContext) -> None:
    anime_name = update.message.text
    search_url = f"{BASE_URL}?s={anime_name.replace(' ', '+')}"
    
    try:
        response = requests.get(search_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find anime results - you'll need to inspect the website to get correct selectors
        results = soup.select('div.post-item')  # This selector might need adjustment
        
        if not results:
            update.message.reply_text(f"Anime '{anime_name}' not found.")
            return
            
        # For simplicity, let's take the first result
        first_result = results[0]
        anime_title = first_result.select_one('h2 a').text
        anime_link = first_result.select_one('h2 a')['href']
        anime_img = first_result.select_one('img')['src']
        
        # Get anime details from the anime page
        anime_details = get_anime_details(anime_link)
        
        # Send anime info to user
        message = f"Found: {anime_title}\n\n{anime_details}"
        update.message.reply_photo(photo=anime_img, caption=message)
        
        # Ask for permission to upload
        keyboard = [
            [InlineKeyboardButton("Yes, upload to DB", callback_data=f"upload_{anime_link}"),
             InlineKeyboardButton("No", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Should I upload this anime to DB channel?', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error searching anime: {e}")
        update.message.reply_text("An error occurred while searching. Please try again.")

def get_anime_details(anime_url: str) -> str:
    try:
        response = requests.get(anime_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract details - these selectors need to be adjusted based on the website structure
        details = []
        
        # Example - get description
        description = soup.select_one('div.entry-content p').text
        details.append(f"Description: {description[:200]}...")  # Limit length
        
        # Add more details as needed
        
        return "\n".join(details)
    except Exception as e:
        logger.error(f"Error getting anime details: {e}")
        return "Could not fetch detailed information."

def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    if query.data.startswith("upload_"):
        anime_link = query.data.split("_")[1]
        query.edit_message_text(text="Starting upload process...")
        
        # Here you would implement the actual upload to DB channel
        # This requires more complex implementation with proper channel permissions
        
        # For now, just simulate
        query.edit_message_text(text=f"Uploading anime from {anime_link} to DB channel...")
        
    elif query.data == "cancel":
        query.edit_message_text(text="Upload cancelled.")

def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    if update.message:
        update.message.reply_text("An error occurred. Please try again.")

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, search_anime))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
