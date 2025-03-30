import os

class Config:
    API_ID = int(os.getenv("API_ID", 22299340))
    API_HASH = os.getenv("API_HASH", "09b09f3e2ff1306da4a19888f614d937")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "7548613937:AAGK2KhZcUnumGQJ-oY5bh8B9ojU4uI8sBQ")
    ADMIN_IDS = [5336360484]  # Your user ID
    CHANNEL_ID = "@animestorys_1"  # Your channel
    VOTE_CHAT_ID = "-1001896877147" # Chat where votes will be counted
