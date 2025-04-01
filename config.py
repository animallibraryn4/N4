import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7632805578:AAHyFiomSTFhIxt56vHnosOREPg2iMU8_TQ")
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "5380609667").split(",") if id]
    DATABASE_URL = os.getenv("DATABASE_URL", "mongodb+srv://n4animeedit:u80hdwhlka5NBFfY@cluster0.jowvb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    SILENT_MODE = os.getenv("SILENT_MODE", "False").lower() == "true"
