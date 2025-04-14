import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def init_db():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
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

def save_fighter(user_id, fighter_name):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )
    cur = conn.cursor()
    cur.execute("INSERT INTO users (user_id, fighter_name) VALUES (%s, %s)", (user_id, fighter_name))
    conn.commit()
    cur.close()
    conn.close()
