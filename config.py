import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "22299340"))
API_HASH = os.getenv("API_HASH", "09b09f3e2ff1306da4a19888f614d937")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7632805578:AAHyFiomSTFhIxt56vHnosOREPg2iMU8_TQ")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://gerbil77001:lkFEusnWzXwe53NU@cluster0.mkeei.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5380609667"))  # Admin user ID
