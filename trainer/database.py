import sqlite3
import logging

logger = logging.getLogger(__name__)

def init_db():
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                nickname TEXT NOT NULL
            )
        """)
        conn.commit()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
    finally:
        conn.close()

def get_nickname(user_id):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nickname FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Ошибка при получении ника для user_id {user_id}: {e}")
        return None
    finally:
        conn.close()

def set_nickname(user_id, nickname):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, nickname) VALUES (?, ?)",
            (user_id, nickname)
        )
        conn.commit()
        logger.info(f"Ник установлен для user_id {user_id}: {nickname}")
    except Exception as e:
        logger.error(f"Ошибка при установке ника для user_id {user_id}: {e}")
    finally:
        conn.close()
