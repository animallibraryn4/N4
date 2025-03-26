import sqlite3
from config import Config

def init_db():
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS anime (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        description TEXT,
        image_url TEXT,
        added_by INTEGER,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anime_id INTEGER,
        quality TEXT NOT NULL,
        file_id TEXT,
        message_id INTEGER,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (anime_id) REFERENCES anime (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_anime(title: str, url: str, description: str, image_url: str, user_id: int):
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO anime (title, url, description, image_url, added_by)
    VALUES (?, ?, ?, ?, ?)
    ''', (title, url, description, image_url, user_id))
    
    conn.commit()
    anime_id = cursor.lastrowid
    conn.close()
    
    return anime_id

def log_upload(anime_id: int, quality: str, file_id: str, message_id: int):
    conn = sqlite3.connect('anime_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO uploads (anime_id, quality, file_id, message_id)
    VALUES (?, ?, ?, ?)
    ''', (anime_id, quality, file_id, message_id))
    
    conn.commit()
    conn.close()
