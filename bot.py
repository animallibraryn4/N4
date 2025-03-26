from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

# Initialize Telegram Bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_video_to_telegram(video_path, caption):
    """Uploads video to Telegram channel."""
    with open(video_path, "rb") as video_file:
        bot.send_video(chat_id=TELEGRAM_CHANNEL_ID, video=video_file, caption=caption)
