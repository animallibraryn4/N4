import sqlite3
import json
import time
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('anime_bot.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_requests INTEGER DEFAULT 0
        )
        ''')
        
        # Queue table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            url TEXT,
            status TEXT DEFAULT 'pending',
            added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            file_path TEXT
        )
        ''')
        
        # Logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            action TEXT,
            details TEXT
        )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id, username, first_name, last_name):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        self.conn.commit()
    
    def increment_request(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE users SET total_requests = total_requests + 1
        WHERE user_id = ?
        ''', (user_id,))
        self.conn.commit()
    
    def add_to_queue(self, user_id, url):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO queue (user_id, url, status)
        VALUES (?, ?, 'pending')
        ''', (user_id, url))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_pending_jobs(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT id, user_id, url FROM queue
        WHERE status = 'pending'
        ORDER BY added_time ASC
        ''')
        return cursor.fetchall()
    
    def update_job_status(self, job_id, status, file_path=None):
        cursor = self.conn.cursor()
        if status == 'processing':
            cursor.execute('''
            UPDATE queue SET status = ?, start_time = CURRENT_TIMESTAMP
            WHERE id = ?
            ''', (status, job_id))
        elif status in ['completed', 'failed']:
            cursor.execute('''
            UPDATE queue SET status = ?, end_time = CURRENT_TIMESTAMP, file_path = ?
            WHERE id = ?
            ''', (status, file_path, job_id))
        self.conn.commit()
    
    def log_action(self, user_id, action, details=""):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO logs (user_id, action, details)
        VALUES (?, ?, ?)
        ''', (user_id, action, details))
        self.conn.commit()
    
    def close(self):
        self.conn.close()

# Global instance
db = Database()
