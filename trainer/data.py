import logging
import os
import psycopg2
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            connect_timeout=5
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                fighter_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

def save_fighter(user_id: int, fighter_name: str):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, fighter_name)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET fighter_name = EXCLUDED.fighter_name;
        """, (user_id, fighter_name))
        conn.commit()
        logger.info(f"Saved fighter: {user_id}, {fighter_name}")
    except Exception as e:
        logger.error(f"Save fighter failed: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()
