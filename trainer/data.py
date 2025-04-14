import psycopg2
from dotenv import load_dotenv
import os
import time
import logging

logger = logging.getLogger(__name__)
load_dotenv()

def init_db():
    for attempt in range(3):
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                connect_timeout=10
            )
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    fighter_name TEXT
                );
                CREATE TABLE IF NOT EXISTS fights (
                    user_id BIGINT,
                    clean_wins INTEGER,
                    partial_success INTEGER,
                    losses INTEGER,
                    hints_used INTEGER
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Database initialized successfully")
            return
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection failed (attempt {attempt + 1}): {e}")
            if attempt < 2:
                time.sleep(5)
            else:
                raise

def save_fighter(user_id, fighter_name):
    for attempt in range(3):
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                connect_timeout=10
            )
            cur = conn.cursor()
            cur.execute("INSERT INTO users (user_id, fighter_name) VALUES (%s, %s)", (user_id, fighter_name))
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"Saved fighter: {user_id}, {fighter_name}")
            return
        except psycopg2.OperationalError as e:
            logger.error(f"Save fighter failed (attempt {attempt + 1}): {e}")
            if attempt < 2:
                time.sleep(5)
            else:
                raise
