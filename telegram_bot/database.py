import aiosqlite
from datetime import datetime

async def init_db():
    async with aiosqlite.connect('ielts_bot.db') as db:
        # Создание таблицы пользователей
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            exam_type TEXT DEFAULT 'academic',
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Создание таблиц для заданий
        await db.execute('''
        CREATE TABLE IF NOT EXISTS listening_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audio_url TEXT,
            questions TEXT,
            answers TEXT,
            difficulty INTEGER
        )
        ''')

        # Аналогичные таблицы для других типов заданий
        # ... 

        await db.commit() 