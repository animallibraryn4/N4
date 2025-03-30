import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from config import Config
from anilist import get_anime_info
from voting import create_voting_keyboard, get_votes
from admin import handle_admin_command, admin_keyboard

app = Client(
    "animebot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Anime Post Command
@app.on_message(filters.command("post") & filters.private)
async def post_anime(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            return await message.reply("Usage: /post <anime_name>")
            
        query = message.text.split(" ", 1)[1]
        img_url, caption = get_anime_info(query)
        
        anime_id = img_url.split("/")[-2]  # Extract AniList ID from URL
        
        # Post to channel with voting buttons
        await client.send_photo(
            Config.CHANNEL_ID,
            img_url,
            caption=caption,
            reply_markup=create_voting_keyboard(anime_id)
        )
        
        await message.reply("Posted successfully to channel!")
        
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

# Voting Handler
@app.on_callback_query(filters.regex(r"vote_(up|down)_(\d+)"))
async def handle_vote(client: Client, callback: CallbackQuery):
    vote_type = callback.data.split("_")[1]
    anime_id = callback.data.split("_")[2]
    
    user_id = callback.from_user.id
    
    # Update votes in database
    # (Implement your voting logic here)
    
    await callback.answer(f"You voted {vote_type} for this anime!")

# Admin Commands
@app.on_message(filters.command(["broadcast", "stats", "ban"]) & filters.user(Config.ADMIN_IDS))
async def admin_commands(client: Client, message: Message):
    await handle_admin_command(client, message)

# Admin Panel
@app.on_message(filters.command("admin") & filters.user(Config.ADMIN_IDS))
async def admin_panel(client: Client, message: Message):
    await message.reply(
        "Admin Panel",
        reply_markup=admin_keyboard()
    )

async def main():
    await app.start()
    print("Bot started!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(mai
