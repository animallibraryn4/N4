from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

votes_db = {}  # In production, use a proper database

def create_voting_keyboard(anime_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👍 Upvote", callback_data=f"vote_up_{anime_id}"),
            InlineKeyboardButton("👎 Downvote", callback_data=f"vote_down_{anime_id}")
        ]
    ])

def get_votes(anime_id):
    return votes_db.get(anime_id, {"up": 0, "down": 0})
